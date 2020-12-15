from flask import Blueprint, jsonify, request
from qanary_helpers.configuration import Configuration
from qanary_helpers.qanary_queries import get_text_question_in_graph, insert_into_triplestore
import pickle


relation_clf = Blueprint('relation_clf', __name__, template_folder='templates')
configfile = "app.conf"
with open("binary/knn.pkl", 'rb') as file:
    knn = pickle.load(file)

with open("binary/vectors.pkl", 'rb') as file:
    vectorizer = pickle.load(file)


configuration = Configuration(configfile, [
    'servicename',
    'serviceversion'
])

@relation_clf.route("/annotatequestion", methods=['POST'])
def qanary_service():

    triplestore_endpoint = request.json["values"]["urn:qanary#endpoint"]
    triplestore_ingraph = request.json["values"]["urn:qanary#inGraph"]
    triplestore_outgraph = request.json["values"]["urn:qanary#outGraph"]

    text = get_text_question_in_graph(triplestore_endpoint=triplestore_endpoint, graph=triplestore_ingraph)[0]['text']
    out = list(knn.predict(vectorizer.transform([text])))[0]

    SPARQLquery = """
                    PREFIX qa: <http://www.wdaqua.eu/qa#>
                    PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
                    PREFIX dbo: <http://dbpedia.org/ontology/>

                    INSERT {{
                    GRAPH <{uuid}> {{
                        ?a oa:relation <{relation_uri}> .
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
        relation_uri=out
    )

    insert_into_triplestore(triplestore_endpoint, triplestore_ingraph,
                            SPARQLquery) 
    return jsonify(request.get_json())
