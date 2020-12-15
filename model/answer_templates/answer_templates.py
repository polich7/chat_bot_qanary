from flask import Blueprint, jsonify, request
from qanary_helpers.configuration import Configuration
from qanary_helpers.qanary_queries import insert_into_triplestore, query_triplestore

import random

t = {
    "birthPlace": ["{0} was born in the {1}", "{1} is the place of birth of {0}"],
	"recordLabel": ["Label of the record {0} is {1}", "{0} was released on the {1}"],
    "genre": ["The ganre of {0} is {1}", "{0} plays in the {1} genre"],
	"producer": ["Producer of {0} is {1}", "{0} is produced by {1}"],
	"writer": ["{0} is written by {1}", "{1} is th writer of {0}"],
	"hometown": ["{0}`s hometown is {1}", "{1} is a hometown of {0}"],
	"deathPlace": ["{0} was died in the {1}", "{1} is the place of death of {0}"],
	"director": ["{0} is derected by {1}", "{1} is director of {0}"],
	"position": ["The position of {0} is {1}","{1} is playing in the position {0}" ],
	"timeZone": ["{0} has the time zone {1}"],
	"location": ["{0} is located in {1}"],
	"author": ["{0} is written by {1}", "The author of {0} is {1}"],
	"literaryGenre": ["{0} is written in the {1} genre", "the ganre of {0} is {1}"],
	"language": ["The language of {0} is {1}"]
}

def make(predicate, subject, objectt):
  print(' Predicate: {} \n Subject: {} \n Result: {}'.format(predicate, subject, objectt))
  if subject == 'tag:/None' or objectt[0] == 'tag:/None':
    return 'Change_question'
  subject = subject.split('/')[-1]
  objectt_s = ''
  for s in objectt:
    objectt_s = '{}{}, '.format(objectt_s, s.split('/')[-1])
  predicate = predicate.split('/')[-1]
  tmps = t[predicate]
  i = random.randint(0, len(tmps)-1)
  return tmps[i].format(subject, objectt_s[:-2]).replace(' ', '_')

natural_language = Blueprint('named_entity_linking', __name__, template_folder='templates')
configfile = "app.conf"

configuration = Configuration(configfile, [
    'servicename',
    'serviceversion'
])

@natural_language.route("/annotatequestion", methods=['POST'])
def qanary_service():

    triplestore_endpoint = request.json["values"]["urn:qanary#endpoint"]
    triplestore_ingraph = request.json["values"]["urn:qanary#inGraph"]
    triplestore_outgraph = request.json["values"]["urn:qanary#outGraph"]


    SPARQLsubj = """
        PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
        SELECT ?p ?o
        FROM <{graph_guid}>
        WHERE 
        {{
            VALUES ?p {{oa:object oa:relation oa:result}} .
            ?s ?p ?o .
        }}""".format(graph_guid=triplestore_ingraph)


    res = None
    res = query_triplestore(triplestore_endpoint + "/query", triplestore_ingraph, SPARQLsubj)
    
    out = []
    for binding in res['results']['bindings']:
        out.append(binding['o']['value'])

    if out[2:] == None:
      out1 = 'I_cannot_find_the_answer.'
    else:
      out1 = make(out[0],out[1],out[2:])


    SPARQLquery = """
                    PREFIX qa: <http://www.wdaqua.eu/qa#>
                    PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
                    PREFIX dbo: <http://dbpedia.org/ontology/>

                    INSERT {{
                    GRAPH <{uuid}> {{
                        ?a oa:answer <{answer_uri}> .
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
        answer_uri=out1
    )

    insert_into_triplestore(triplestore_endpoint, triplestore_ingraph,
                            SPARQLquery) 
    return jsonify(request.get_json())

