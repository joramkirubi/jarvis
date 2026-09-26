'use strict';
let googleVersion = '', googleBusy = false;
function proposalText(item) {
  const p = item.payload;
  if (item.kind === 'email') return `From account: ${p.account}\nTo: ${p.to.join(', ')}\nSubject: ${p.subject}\n\n${p.body}`;
  return `Calendar account: ${p.account} (primary)\nTitle: ${p.summary}\nStart: ${p.start.dateTime}\nEnd: ${p.end.dateTime}\nInvitations to: ${p.attendees.map(a=>a.email).join(', ') || 'No attendees'}\n\n${p.description}`;
}
async function refreshGoogle() {
  if (googleBusy) return;
  googleBusy = true;
  try {
    const data = await api('google');
    $('googleStatus').textContent = data.connected ? 'Connected: '+data.email+' · '+data.message : data.message;
    $('googleInbox').disabled = $('googleCalendar').disabled = !data.connected;
    const signature = JSON.stringify(data.proposals);
    if (signature !== googleVersion) {
      googleVersion = signature;
      const area = $('googleProposals'); area.replaceChildren();
      if (!data.proposals.length) area.append(node('p','No drafts yet. Ask Jarvis to draft an email or schedule a meeting.','empty-note'));
      for (const item of data.proposals) {
        const row = node('article', undefined, 'google-proposal');
        const states = {pending:'AWAITING YOUR APPROVAL',done:'COMPLETED',rejected:'REJECTED',cancelled:'CANCELLED',expired:'EXPIRED',executing:'IN PROGRESS — check Google if this persists',check_google:'OUTCOME UNKNOWN — check Google before trying again'};
        row.append(node('strong',(item.kind==='email'?'EMAIL':'EVENT')+' · '+(states[item.state] || item.state)),node('pre',proposalText(item)));
        if (item.state === 'pending') {
          const buttons = node('div',undefined,'controls');
          const approve = node('button',item.kind==='email'?'Confirm & send email':'Confirm & create event','primary');
          const reject = node('button','Reject');
          for (const [button, decision] of [[approve,true],[reject,false]]) {
            button.addEventListener('click',async()=>{
              if (decision && !confirm(proposalText(item)+'\n\n'+(item.kind==='email'?'Send this email now?':'Create this event and send the listed invitations?'))) return;
              approve.disabled = reject.disabled = true;
              const result = await action('google/decision',{id:item.id,approve:decision});
              if (result) toast(result.message);
              googleVersion = ''; await refreshGoogle();
            });
            buttons.append(button);
          }
          row.append(buttons);
        }
        area.append(row);
      }
    }
  } catch (error) { $('googleStatus').textContent=error.message; }
  finally { googleBusy = false; }
}
async function googleRead(actionName) {
  const button = actionName==='search_email' ? $('googleInbox') : $('googleCalendar');
  button.disabled = true;
  $('googleResults').replaceChildren(node('p','Reading Google…'));
  try {
    const result = await api('google/read',{action:actionName,query:'is:unread'});
    if (!result.ok) throw new Error(result.message);
    const area = $('googleResults'); area.replaceChildren();
    if (actionName==='search_email') {
      if (!result.items.length) area.append(node('p','No unread emails found.'));
      for (const item of result.items) {
        const header = name => (item.headers.find(h=>h.name.toLowerCase()===name)||{}).value || '';
        const row = node('article',undefined,'google-proposal');
        row.append(node('strong',header('subject')||'(No subject)'),node('p',header('from')),node('p',item.snippet)); area.append(row);
      }
    } else {
      if (!result.events.length) area.append(node('p','No events in this range on your primary calendar.'));
      for (const item of result.events) area.append(node('pre',(item.summary||'(Untitled)')+'\n'+(item.start.dateTime||item.start.date)+' → '+(item.end.dateTime||item.end.date)));
    }
    if (result.more_available) area.append(node('p','More results exist. Ask Jarvis for a narrower search or date range.'));
  } catch(error) { $('googleResults').replaceChildren(node('p',error.message)); }
  finally { await refreshGoogle(); }
}
$('refreshGoogle').addEventListener('click',refreshGoogle);
$('googleInbox').addEventListener('click',()=>googleRead('search_email'));
$('googleCalendar').addEventListener('click',()=>googleRead('list_events'));
refreshGoogle(); setInterval(refreshGoogle,5000);
