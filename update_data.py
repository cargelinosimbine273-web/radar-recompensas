import json, os, sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def get(url):
    headers = {'User-Agent': 'Radar-Recompensas/1.0', 'Accept': 'application/json'}
    if url.startswith('https://api.github.com/') and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
        headers['Accept'] = 'application/vnd.github+json'
    with urlopen(Request(url, headers=headers), timeout=40) as response: return json.load(response)

def save(name, obj):
    os.makedirs('data', exist_ok=True)
    with open('data/' + name + '.json', 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False)

now = datetime.now(timezone.utc).isoformat()
errors = []
try:
    raw = get('https://remotive.com/api/remote-jobs?limit=100')
    jobs = [{'id':j['id'],'title':j.get('title',''),'company':j.get('company_name',''),'location':j.get('candidate_required_location') or 'Não informado','salary':j.get('salary') or 'Não informado','url':j['url'],'published':j.get('publication_date','')} for j in raw['jobs'] if j.get('url','').startswith('https://remotive.com/')]
    save('news', {'items':jobs,'checked_at':now,'error':None})
except Exception as e: errors.append('Remotive: '+str(e))
try:
    q = urlencode({'q':'label:bounty state:open type:issue','sort':'updated','order':'desc','per_page':100})
    raw = get('https://api.github.com/search/issues?' + q)
    issues = [{'title':i['title'],'url':i['html_url'],'repo':i.get('repository_url','').split('/repos/')[-1],'updated':i['updated_at'],'labels':[l['name'] for l in i.get('labels',[])],'body':(i.get('body') or '')[:5000]} for i in raw['items']]
    save('opportunities', {'items':issues,'fetched_at':now,'incomplete':raw.get('incomplete_results',False)})
except Exception as e: errors.append('GitHub: '+str(e))
if errors:
    print('\n'.join(errors),file=sys.stderr)
    sys.exit(1)
print('Dados atualizados:',now)
