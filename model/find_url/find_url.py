from flask import Blueprint, jsonify, request
from qanary_helpers.configuration import Configuration
from qanary_helpers.qanary_queries import get_text_question_in_graph, insert_into_triplestore
import requests

def res(text, confidence):
  params = {'text' : text, 'confidence' : confidence}
  response = requests.get(url='http://webengineering.ins.hs-anhalt.de:43720/rest/annotate',
                          params=params,
                          headers={'accept': 'application/json'},
                          verify=False)
  response = response.json()
  return response

def get_urls(data):
  out = []
  if 'Resources' in data.keys():
    data = data['Resources']
    for i in data:
      out.append({i['@URI'] : i['@surfaceForm']})
    return out

def make(question):
    question1 = None
    question1 = get_urls(res(question, 0.7))
    if question1 is None:
        return None
    else:
        return list(question1[0].keys())[0]
named_entity_linking = Blueprint('named_entity_linking', __name__, template_folder='templates')
configfile = "app.conf"

configuration = Configuration(configfile, [
    'servicename',
    'serviceversion'
])

@named_entity_linking.route("/annotatequestion", methods=['POST'])
def qanary_service():

    triplestore_endpoint = request.json["values"]["urn:qanary#endpoint"]
    triplestore_ingraph = request.json["values"]["urn:qanary#inGraph"]
    triplestore_outgraph = request.json["values"]["urn:qanary#outGraph"]

    text = get_text_question_in_graph(triplestore_endpoint=triplestore_endpoint, graph=triplestore_ingraph)[0]['text']

    out = make(text)


    SPARQLquery = """
                    PREFIX qa: <http://www.wdaqua.eu/qa#>
                    PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
                    PREFIX dbo: <http://dbpedia.org/ontology/>

                    INSERT {{
                    GRAPH <{uuid}> {{
                        ?a oa:object <{object_uri}> .
                        ?a oa:annotatedBy <urn:qanary:{app_name}> .
                        ?a oa:annotatedAt ?time .
                        }}
                    }}
                    WHERE {{
                        BIND (IRI(str(RAND())) AS ?a) .
                        BIND (now() as ?time) 
                    }}
                """.format(
        uuid=triplestore_ingraph,
        app_name="{0}:{1}:Python".format(configuration.servicename, configuration.serviceversion),
        object_uri=out
    )

    insert_into_triplestore(triplestore_endpoint, triplestore_ingraph,
                            SPARQLquery) 
    return jsonify(request.get_json())
