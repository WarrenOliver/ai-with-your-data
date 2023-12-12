from flask import Flask, render_template, request, redirect, url_for
from cbot import get_response


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        chat_history = get_response()
        answer_text = "Answer: "
        return render_template("index.html", chat_history=chat_history, answer_text=answer_text)

    else:
        return render_template('index.html')




if __name__ == '__main__':
    app.run(debug=True) 