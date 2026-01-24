import mailbox
import email.utils
import re
from datetime import datetime
import json

# Parse the MBOX file
mbox_path = r"d:\Dev\Repos\vcaboara.github.io\gmail_takeout\Takeout\Mail\ACS.mbox"
mbox = mailbox.mbox(mbox_path)

# Entities to search for
entities = [
    # Federal
    ('USDA', ['usda.gov', 'usda', 'biopreferred']),
    ('DOE', ['energy.gov', 'doe.gov', 'bioenergy']),
    ('BETO', ['beto', 'bioenergy technologies']),
    # Commercial US
    ('Pfizer', ['pfizer.com']),
    ('Novartis', ['novartis.com']),
    ('Genentech', ['genentech.com', 'gene.com']),
    ('Amgen', ['amgen.com']),
    ('Gilead', ['gilead.com']),
    ('Regeneron', ['regeneron.com']),
    ('Moderna', ['moderna.com', 'modernatx.com']),
    ('BioNTech', ['biontech.com']),
    # Gov entities
    ('Riverside County', ['riversideca.gov', 'riverside']),
    ('Rep Calvert', ['calvert', 'house.gov']),
]

notices = []

for message in mbox:
    # Extract headers
    from_header = message.get('From', '')
    to_header = message.get('To', '')
    cc_header = message.get('Cc', '')
    subject = message.get('Subject', '')
    date_str = message.get('Date', '')
    
    # Check if sent from vcaboara
    if 'vcaboara' not in from_header.lower():
        continue
    
    # Parse date
    try:
        date_tuple = email.utils.parsedate_to_datetime(date_str)
        date_formatted = date_tuple.strftime('%Y-%m-%d %H:%M')
    except:
        date_formatted = date_str[:50] if date_str else 'Unknown'
    
    # Combine recipient fields
    all_recipients = f"{to_header} {cc_header}"
    
    # Get message body
    body = ""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = str(message.get_payload())
    
    # Check for entity mentions
    for entity_name, keywords in entities:
        for keyword in keywords:
            if keyword.lower() in all_recipients.lower() or keyword.lower() in body.lower()[:500]:
                # Check for bounce/error
                is_bounced = any(term in subject.lower() or term in body[:1000].lower() 
                               for term in ['undeliverable', 'delivery failed', 'error', 'bounce', 
                                          'rejected', 'not delivered', '5.4.14'])
                
                notices.append({
                    'entity': entity_name,
                    'date': date_formatted,
                    'subject': subject[:100],
                    'to': to_header[:100],
                    'bounced': is_bounced,
                    'body_preview': body[:200].strip()
                })
                break  # Only record once per entity per email

# Sort by date
notices.sort(key=lambda x: x['date'])

# Print results
print(f"\n=== Found {len(notices)} notice emails ===\n")
for notice in notices:
    status = "❌ BOUNCED" if notice['bounced'] else "✓ Delivered"
    print(f"{status} | {notice['entity']:<20} | {notice['date']} | {notice['subject']}")
    print(f"   To: {notice['to']}")
    print()

# Save to JSON
with open('notices_extracted.json', 'w') as f:
    json.dump(notices, f, indent=2)

print(f"\nSaved to notices_extracted.json")
