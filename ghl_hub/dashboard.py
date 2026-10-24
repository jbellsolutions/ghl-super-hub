"""Dashboard deep links so browser agents open the right page instead of hunting menus.

Routes are HighLevel's known v2 URL patterns, not live-verified per account. White-label
menus, plan limits and UI releases can differ: always confirm the loaded page, and fall
back to the menu path when a route redirects or 404s.
"""
import os
import re
from urllib.parse import quote
from . import knowledge

# key: (route under /v2/location/{location}/, sidebar menu path, docs search query, skill)
PAGES={
 'dashboard':('dashboard','Dashboard','dashboard widgets','ghl-operator'),
 'conversations':('conversations/conversations','Conversations','conversations inbox','ghl-operator'),
 'contacts':('contacts/smart_list/All','Contacts > Smart Lists','smart list contacts','ghl-operator'),
 'contact':('contacts/detail/{id}','Contacts > (open contact)','contact details page','ghl-operator'),
 'opportunities':('opportunities/list','Opportunities','opportunities pipeline','ghl-operator'),
 'calendars':('calendars/view','Calendars','calendar appointments','ghl-operator'),
 'calendar_settings':('settings/calendars','Settings > Calendars','calendar settings','ghl-operator'),
 'workflows':('automation/workflows','Automation > Workflows','workflow','ghl-workflows'),
 'workflow':('automation/workflows/{id}','Automation > Workflows > (open workflow)','workflow builder actions','ghl-workflows'),
 'funnels':('funnels-websites/funnels','Sites > Funnels','funnel builder','ghl-sites'),
 'websites':('funnels-websites/websites','Sites > Websites','website builder','ghl-sites'),
 'forms':('form-builder/main','Sites > Forms','form builder','ghl-sites'),
 'surveys':('survey-builder/main','Sites > Surveys','survey builder','ghl-sites'),
 'blogs':('blogs','Sites > Blogs','blog posts','ghl-sites'),
 'email_campaigns':('marketing/emails/campaigns','Marketing > Emails > Campaigns','email campaign','ghl-email'),
 'email_templates':('marketing/emails/templates','Marketing > Emails > Templates','email template builder','ghl-email'),
 'social_planner':('marketing/social-planner','Marketing > Social Planner','social planner','ghl-operator'),
 'courses':('memberships/courses/products','Memberships > Courses > Products','course products','ghl-courses'),
 'communities':('communities/groups','Memberships > Communities','communities group','ghl-memberships'),
 'affiliates':('affiliate-manager/dashboard','Marketing > Affiliate Manager','affiliate manager','ghl-affiliates'),
 'invoices':('payments/invoices','Payments > Invoices','invoices','ghl-operator'),
 'products':('payments/products','Payments > Products','payment products','ghl-operator'),
 'reputation':('reputation/overview','Reputation','reputation reviews','ghl-operator'),
 'reporting':('reporting/reports','Reporting','reporting','ghl-operator'),
 'media':('media-storage','Media Storage','media library','ghl-operator'),
 'settings':('settings/company','Settings > Business Profile','business profile settings','ghl-operator'),
 'staff':('settings/staff/team','Settings > My Staff','team users permissions','ghl-operator'),
 'pipelines':('settings/pipelines','Settings > Pipelines','pipelines','ghl-operator'),
 'custom_fields':('settings/fields','Settings > Custom Fields','custom fields','ghl-operator'),
 'custom_values':('settings/custom_values','Settings > Custom Values','custom values','ghl-operator'),
 'tags':('settings/tags','Settings > Tags','tags','ghl-operator'),
 'integrations':('settings/integrations','Settings > Integrations','integrations','ghl-operator'),
 'private_integrations':('settings/private-integrations','Settings > Private Integrations','private integrations token','ghl-api'),
 'phone_numbers':('settings/phone_number','Settings > Phone Numbers','phone numbers','ghl-operator'),
 'email_services':('settings/smtp_service','Settings > Email Services','email services dedicated domain','ghl-email'),
 'domains':('settings/domain','Settings > Domains','domain setup','ghl-sites'),
}

def app_origin():
    domain=os.environ.get('GHL_APP_DOMAIN','app.gohighlevel.com').strip().lower().removeprefix('https://').rstrip('/')
    if not re.fullmatch(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+',domain): raise ValueError('GHL_APP_DOMAIN must be a hostname such as app.gohighlevel.com')
    return 'https://'+domain

def page(page,resource_id=None,location_id=None,docs=3):
    name=page
    if name not in PAGES: raise ValueError('Unknown page; choose one of: '+', '.join(sorted(PAGES)))
    route,menu,query,skill=PAGES[name]
    location=location_id or os.environ.get('GHL_LOCATION_ID','')
    if not location or location=='YOUR_LOCATION_ID': raise ValueError('Set GHL_LOCATION_ID or pass location_id')
    if '{id}' in route:
        if not resource_id: raise ValueError(name+' needs resource_id')
        route=route.replace('{id}',quote(str(resource_id),safe=''))
    result=dict(page=name,url=app_origin()+'/v2/location/'+quote(location,safe='')+'/'+route,menu_path=menu,skill=skill,
        verify='Unverified URL pattern. After loading, confirm the page heading and that the account switcher shows this location; if redirected or blank, navigate by menu_path.')
    if docs:
        try: result['help']=[{k:r.get(k) for k in ('title','url')} for r in knowledge.search(query,docs)]
        except Exception: result['help']=[]
    return result

def pages(): return [dict(page=k,menu_path=v[1],needs_id='{id}' in v[0],skill=v[3]) for k,v in sorted(PAGES.items())]
