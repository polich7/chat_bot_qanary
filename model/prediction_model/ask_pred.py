import requests
from qanary_helpers.qanary_queries import query_triplestore
import json

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
            VALUES ?p {{oa:relation}} .
            ?s ?p ?o .
        }}""".format(graph_guid=in_graph)

    return get_text_response(triplestore_endpoint=endpoint,
                             graph=in_graph,
                             SPARQLquery=SPARQLquery)

def ask(question_text):
  response = requests.post(url=qanary_pipeline_url,
                             params={
                                 "question": question_text,
                                 "componentlist[]": ["find_url_fominykh","prediction_model_fominykh"]
                             }).json()
  result = get_final_result(response['endpoint'], response['inGraph'])
  return json.dumps({'answer': result})
