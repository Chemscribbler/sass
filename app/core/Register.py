from flask import Flask, render_template, request
from id_importer import get_all_ids

app = Flask(__name__)
app.debug = True


@app.route("/", methods=["POST", "GET"])
def reg_players():
    corps, runners = get_all_ids()
    return render_template("register.html", corps=corps, runners=runners)


if __name__ == "__main__":
    app.run()
