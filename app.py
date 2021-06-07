from flask import Flask, redirect, url_for, render_template, request
import covidapp
import dataset
import os.path
from os import path
import vaxx


app = Flask(__name__)
app.secret_key = 'hello'

@app.route("/")
def home():
	if path.exists("vaxxdataset.csv") == False:
		vaxx.create_vaxx_data().to_csv('vaxxdataset.csv')
	return render_template("index.html")


@app.route("/countyinfo", methods = ['POST', 'GET'])
def countyinfo():
	if path.exists("vaxxdataset.csv") == False:
		vaxx.create_vaxx_data().to_csv('vaxxdataset.csv')
	
	if request.method == "POST":
		county = request.form["cty"]
		if county == '':
			return render_template('empty.html')

		if path.exists("fulldataset.csv") == False:
			dataset.main_function().to_csv('fulldataset.csv')

		embed_vaxx = covidapp.vaxx_plot(county)
		allinfo = covidapp.county_stats(county)
		if len(allinfo) == 6:
			tbl, stat, info, rec, risk_pos, pct = allinfo
			ctyrisk_pos = risk_pos - 65
			lnrisk_pos = risk_pos - 20
			return render_template("result.html", county = county, tbl = [tbl.to_html(classes='data', header = True)], stat = stat, info = info, rec = rec, risk_pos = risk_pos, pct = pct, ctyrisk_pos = ctyrisk_pos, lnrisk_pos = lnrisk_pos)
		else:
			return render_template("undef_result.html", issue = allinfo)
	else:
		ctys = covidapp.county_list()
		return render_template("data.html", ctys = ctys)
		#return render_template("data.html", states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'])
		

@app.route("/about")
def about():
	if path.exists("vaxxdataset.csv") == False:
		vaxx.create_vaxx_data().to_csv('vaxxdataset.csv')

	return render_template("about.html")

@app.route("/stats", methods = ['POST', 'GET'])
def stats():
	if path.exists("vaxxdataset.csv") == False:
		vaxx.create_vaxx_data().to_csv('vaxxdataset.csv')
	if request.method == "POST":
		if path.exists("fulldataset.csv") == False:
			dataset.main_function().to_csv('fulldataset.csv')
		# FIX LOAD DATASET
		top10, bot10 = covidapp.usplot()
		date = covidapp.multivaxx_plot()
		return render_template("stats.html", top10 = [top10.to_html(classes='data', header = True)], bot10 = [bot10.to_html(classes='data', header = True)], date = date)
	else:
		return render_template("statshome.html")


if __name__ == '__main__':
    app.run(debug = True)
