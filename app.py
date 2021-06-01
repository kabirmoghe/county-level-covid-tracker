from flask import Flask, redirect, url_for, render_template, request
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
		covidapp.vaxx_plot(county)
		allinfo = covidapp.county_stats(county)
		if len(allinfo) == 5:
			tbl, stat, info, rec, img = allinfo
			return render_template("result.html", county = county, tbl = [tbl.to_html(classes='data', header = True)], stat = stat, info = info, rec = rec, img = img)
		else:
			return render_template("undef_result.html", issue = allinfo)
	else:
		ctys = covidapp.county_list()
		return render_template("data.html", ctys = ctys)
		#return render_template("data.html", states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'])
		

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/stats")
def stats():
	top10, bot10 = covidapp.usplot()
	covidapp.multivaxx_plot()
	return render_template("plot.html", top10 = [top10.to_html(classes='data', header = True)], bot10 = [bot10.to_html(classes='data', header = True)])

if __name__ == '__main__':
    app.run(debug = True)
