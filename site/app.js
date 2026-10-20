'use strict';
const plans={
 funnel:{tag:'SITES + API + WORKFLOWS',steps:[['Build the page','Create the funnel and form in the dashboard.'],['Connect the journey','Wire the conversion to the right contact and workflow.'],['Test the conversion','Submit a test lead and verify the downstream result.'],['Publish with evidence','Check the live URL, mobile layout, and saved state.']]},
 nurture:{tag:'EMAIL + WORKFLOWS + API',steps:[['Prepare the content','Create or update templates with documented API operations.'],['Build the sequence','Configure triggers, branches, waits, and email actions in the UI.'],['Test with a contact','Check merge fields, timing, delivery, and exit conditions.'],['Verify the final state','Read back configuration and record test evidence.']]},
 course:{tag:'COURSES + MEMBERSHIPS + WORKFLOWS',steps:[['Build the curriculum','Author lessons in the dashboard or inspect the course importer.'],['Configure the offer','Connect the right course, pricing, and access rules.'],['Automate enrollment','Set up supported grant and revoke actions through workflows.'],['Become the learner','Test login, content access, drip behavior, and revocation.']]}
};
const tabs=[...document.querySelectorAll('[data-journey]')];
function activate(tab){
 tabs.forEach(item=>{item.setAttribute('aria-selected',String(item===tab));item.tabIndex=item===tab?0:-1;});
 const plan=plans[tab.dataset.journey];document.querySelector('#journey-tag').textContent=plan.tag;
 document.querySelector('#journey-panel').setAttribute('aria-labelledby',tab.id);
 const steps=document.querySelector('#journey-steps');steps.replaceChildren();
 plan.steps.forEach(([title,body],index)=>{const li=document.createElement('li'),number=document.createElement('span'),h=document.createElement('h3'),p=document.createElement('p');number.textContent=String(index+1).padStart(2,'0');h.textContent=title;p.textContent=body;li.append(number,h,p);steps.append(li);});
}
tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>activate(tab));tab.addEventListener('keydown',event=>{let target;if(event.key==='ArrowRight')target=tabs[(index+1)%tabs.length];if(event.key==='ArrowLeft')target=tabs[(index+tabs.length-1)%tabs.length];if(event.key==='Home')target=tabs[0];if(event.key==='End')target=tabs.at(-1);if(target){event.preventDefault();activate(target);target.focus();}});});
const copy=document.querySelector('#copy-command');
copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.querySelector('#install-command').textContent);copy.textContent='Copied ✓';document.querySelector('#copy-feedback').textContent='Installation commands copied.';setTimeout(()=>{copy.textContent='Copy ⧉';},2200);}catch{document.querySelector('#copy-feedback').textContent='Select the installation commands and copy them manually.';copy.textContent='Select text to copy';}});
