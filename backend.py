from flask import Flask, request, redirect, url_for, render_template, jsonify
import requests
from qanary_helpers.qanary_queries import query_triplestore
import json

app = Flask(__name__)  

qanary_pipeline_url = "http://webengineering.ins.hs-anhalt.de:43740/startquestionansweringwithtextquestion"


def get_text_response(triplestore_endpoint, graph, SPARQLquery):
    text_response = None
    result = query_triplestore(triplestore_endpoint + "/query", graph, SPARQLquery)

    for binding in result['results']['bindings']:
        text_response = binding['o']['value']

    return text_response


def get_final_result(endpoint, in_graph):
    SPARQLquery = """
        PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
        SELECT ?p ?o
        FROM <{graph_guid}>
        WHERE 
        {{
            VALUES ?p {{oa:answer}} .
            ?s ?p ?o .
        }}""".format(graph_guid=in_graph)

    return get_text_response(triplestore_endpoint=endpoint,
                             graph=in_graph,
                             SPARQLquery=SPARQLquery)

@app.route('/health', methods=['GET'])
def index():
  print('OK')
  return jsonify({'status': 'OK'})

def ask(question_text):
  response = requests.post(url=qanary_pipeline_url,
                             params={
                                 "question": question_text,
                                 "componentlist[]": ["find_url_fominykh","prediction_model_fominykh",
                                                      "sparql_query_fominykh","answer_templates_fominykh"]
                             }).json()
  result = get_final_result(response['endpoint'], response['inGraph'])
  return json.dumps({'answer': result})

@app.route('/question', methods=['POST'])
def question():
  data = request.data
  question = json.loads(data)['question']
  answer = json.loads(ask(question).replace('_', ' '))
  if answer is None:
    answer = 'Change question'
  else:
    answer = answer['answer'][5:]
    print(answer)
  text = {
  'question_text': question,
  'answer_text': answer,
  }
  return jsonify(text)

if __name__ == "__main__":
  app.run(host = '127.0.0.2', port = 8000, debug = True)