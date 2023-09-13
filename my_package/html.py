import base64
import os

logo_image = os.path.abspath("./app/static/actum-keboola.png")

#logo_image = os.path.abspath("./static/actum-keboola.png")
logo_html = f"""<div style="display: flex; justify-content: center;">


 <img src="data:image/png;base64,{base64.b64encode(open(logo_image, "rb").read()).decode()}" 
         style="width: 550px; margin-right: 20px; margin-bottom:50px;margin-up:50px 
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 0.5px;
                transition: transform 0.3s ease, box-shadow 0.3s ease;">             
              
</div>
"""

html_code = '''
<div style="display: flex; justify-content: center;">
    <div style="width: 47%;text-align:left;padding-right:3%">
        <span style="font-size:1.2em;"><strong style="display:inline-block; padding-bottom: 4%;">Filters:</strong></span>
        <p><strong>Source</strong> refers to the origin or channel through which users interact with an advertisement or visit a website.</p>
        <p><strong>Domain </strong>refers to the website address or URL where an advertisement or marketing campaign directs users when they click on the advertisement.</p>
    </div>
    <div style="width: 47%;text-align:left;padding-left:3%">
    <span style="font-size:1.2em;"><strong style="display:inline-block; padding-bottom: 4%;">Metrics:</strong></span>
        <p><strong>Clicks</strong> refer to the number of times users click on an advertisement or a specific ad element, such as a headline, image, or call-to-action button.</p>
        <p><strong>Impressions</strong> refer to the number of times an advertisement is displayed or shown to users within the platform's network or on websites that participate in the advertising program.</p>
        <p><strong>Cost-Per-Click (CPC)</strong> refers to  the amount advertisers pay for each click on their advertisements.</p>
    </div>
</div>
'''

html_footer = f"""
 <div style="display: flex; justify-content: flex-end;margin-top: 12%">
        <div>
            <p><strong>Version:</strong> 1.1</p>
        </div>
        <div style="margin-left: auto;">
            
        </div>
    </div>
"""

title = {
    "filter":'<p class="subheader">Filters</p>',
    "statistic":'<p class="subheader">Statistics</p>',
    "charts":'<p class="subheader">Charts</p>',
    "clicks":'<p class="subheader">Clicks</p>',
    "impressions":'<p class="subheader">Impressions</p>',
    "clicktr":'<p class="subheader">Click-Through Rate</p>',
    "campaignsPerClick":'<p class="subheader">Top 10 Campaigns</p>',
    "rawData":'<p class="subheader">Raw data</p>',
    "description":'<p class="subheader">Description</p>',
    "sourcesPerClick":'<p class="subheader">Top 10 Marketing Sources</p>',
    "topcampaigns":'<p class="subheader">Top Performing Campaigns</p>',
    "inputdata":'<p class="subheader">Filtered data </p>'
}
