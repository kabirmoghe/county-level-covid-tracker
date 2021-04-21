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
		allinfo = covidapp.county_stats(county)
		if len(allinfo) == 3:
			tbl, stat, info = allinfo
			return render_template("result.html", county = county, tbl = [tbl.to_html(classes='data', header = True)], stat = stat, info = info)
		else:
			return render_template("undef_result.html", issue = allinfo)
	else:
		return render_template("data.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == '__main__':
    app.run(debug = True)
