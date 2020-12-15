from flask import Flask, request,  render_template
import requests


SERVER_IP = 'http://127.0.0.2:8000/'

app = Flask(__name__)  

def check(url):
  url = '{}health'.format(url)
  try:
    response = requests.get(url=url)
    out = response.json()
    return out
  except:
    return {'status': 'NOT_OK'}

def answer(url, question_text):
  data = {'question': question_text}
  response = requests.post(url=url, json=data)
  out = response.json()
  return out

@app.route('/', methods=['GET', 'POST'])
def index():
  text = ''
  if request.method == 'POST':
    text = check(SERVER_IP)
    question = request.form['question']
    if question != '': 
      text = check(SERVER_IP)
      if text['status'] == 'OK':
        text = answer(SERVER_IP + 'question', question)
        text = render_template('answer_type.html').format(text['question_text'],
                                                            text['answer_text'])
  return render_template('question.html') % text

if __name__ == "__main__":
  app.run(host = '127.0.0.2', port = 5000, debug = True)