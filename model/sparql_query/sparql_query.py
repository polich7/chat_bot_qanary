from flask import Blueprint, jsonify, request
from qanary_helpers.configuration import Configuration
from qanary_helpers.qanary_queries import  insert_into_triplestore, query_triplestore

from SPARQLWrapper import SPARQLWrapper, JSON

def SPARQL(subject, predicate):
  response_array = list()
  sparql = SPARQLWrapper("http://dbpedia.org/sparql")
  sparql.setQuery("""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?result ?objLabel
WHERE
{
  <%s> <%s> ?result .  
  ?result rdfs:label ?objLabel .
  filter(LANG(?objLabel) = "en") .
}
""" % (subject, predicate))
  sparql.setReturnFormat(JSON)
  print("""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?result ?objLabel
WHERE
{
  <%s> <%s> ?result .  
  ?result rdfs:label ?objLabel .
  filter(LANG(?objLabel) = "en") .
}
""" % (subject, predicate))
  results = sparql.query().convert()
  result = ''
  for res in results["results"]["bindings"]:
    result = '{}{}>, <'.format(result, res['result']['value'])
  if len(result) > 0:
    result = result[:-4]
  else:
    result = None

  return result

sparql_query = Blueprint('named_entity_linking', __name__, template_folder='templates')

configfile = "app.conf"

configuration = Configuration(configfile, [
    'servicename',
    'serviceversion'
])

@sparql_query.route("/annotatequestion", methods=['POST'])
def qanary_service():

    triplestore_endpoint = request.json["values"]["urn:qanary#endpoint"]
    triplestore_ingraph = request.json["values"]["urn:qanary#inGraph"]
    triplestore_outgraph = request.json["values"]["urn:qanary#outGraph"]

    SPARQLquery = """
        PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
        SELECT ?p ?o
        FROM <{graph_guid}>
        WHERE 
        {{
            VALUES ?p {{oa:relation oa:object}} .
            ?s ?p ?o .
        }}""".format(graph_guid=triplestore_ingraph)

    res = None
    res = query_triplestore(triplestore_endpoint + "/query", triplestore_ingraph, SPARQLquery)['results']['bindings']

    res[0] = res[0]['o']['value']
    res[1] = res[1]['o']['value']


    out = SPARQL(res[1], res[0])
    if out == None: 
      out = 'None'
    else:
      out = out

    SPARQLquery = """
                    PREFIX qa: <http://www.wdaqua.eu/qa#>
                    PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
                    PREFIX dbo: <http://dbpedia.org/ontology/>

                    INSERT {{
                    GRAPH <{uuid}> {{
                        ?a oa:result <{result_uri}> .
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
        result_uri=out
    )

    insert_into_triplestore(triplestore_endpoint, triplestore_ingraph,
                            SPARQLquery) 
    return jsonify(request.get_json())
