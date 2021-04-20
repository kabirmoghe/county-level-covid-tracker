from flask import Flask, redirect, url_for, render_template, request, session
from datetime import timedelta
import covidapp

app = Flask(__name__)
app.secret_key = 'hello'

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/countyinfo", methods = ['POST', 'GET'])
def countyinfo():
	if request.method == "POST":
		county = request.form["cty"]
		if len(covidapp.county_stats(county)) == 2:
			stat, info = covidapp.county_stats(county)
			return render_template("result.html", county = county, stat = stat, info = info)
		else:
			issue = covidapp.county_stats(county)
			return render_template("undef_result.html", issue = issue)
	else:
		return render_template("data.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug = True)
