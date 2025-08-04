import os
import smtplib
import html
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))  # Cast to int, default to 465
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

def generate_script_tag(bot_id: str, name: str) -> str:
    """Generate the script tag for embedding the chatbot."""
    return f'<script src="https://www.upindersangha.com/docative-widget.js" data-bot-id="{bot_id}" data-name="{name}"></script>'

def send_embed_script_email(to_email: str, bot_id: str, name: str) -> None:
    """Send an email with the chatbot embed script tag."""
    # Escape user inputs for safety
    safe_name = html.escape(name)
    safe_to_email = html.escape(to_email)
    script_tag = generate_script_tag(bot_id, name)
    safe_script_tag = html.escape(script_tag)  # Escape for HTML rendering
    # Create multipart/alternative email
    msg = MIMEMultipart('alternative')
    msg["Subject"] = "Your Docative Chatbot is Ready! 🚀"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Reply-To"] = SENDER_EMAIL
    msg["MIME-Version"] = "1.0"
    # HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Docative Chatbot is Ready!</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: bold;
                font-size: 20px;
                width: 40px;
                height: 40px;
                line-height: 40px;
                border-radius: 8px;
                margin-bottom: 10px;
            }}
            .content {{
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            .code-block {{
                background-color: #f0f0f0;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 15px 0;
                font-family: 'Courier New', Courier, monospace;
                font-size: 14px;
                overflow-x: auto;
                white-space: pre;
            }}
            .integration-section {{
                margin-top: 25px;
            }}
            .integration-section h3 {{
                color: #667eea;
                margin-bottom: 10px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: #888;
            }}
            .cta {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">D</div>
            <h1>Docative</h1>
            <p>Make Your Documents Talk Back</p>
        </div>
        
        <div class="content">
            <h2>Hi {safe_name},</h2>
            <p>Thank you for using Docative! Your custom chatbot is now ready to be embedded on your website. Simply copy and paste the script tag below into your website's HTML where you want the chatbot to appear.</p>
            
            <pre class="code-block">{safe_script_tag}</pre>
            
            <p>That's it! Your chatbot will now appear on your website and can answer questions based on the document you uploaded.</p>
            
            <div class="integration-section">
                <h3>Integration Guides</h3>
                <p>For specific platforms, here are the simplest integration methods:</p>
                
                <h4>HTML / Static Website</h4>
                <p>Paste the script tag just before the closing &lt;/body&gt; tag of your HTML file.</p>
                
                <h4>Vue.js</h4>
<p>Add this to your page component or app.vue:</p>
<pre class="code-block">&lt;script setup&gt;
import {{ onMounted }} from 'vue';

onMounted(() =&gt; {{
  const script = document.createElement('script');
  script.src = 'https://www.upindersangha.com/docative-widget.js';
  script.async = true;
  script.setAttribute('data-bot-id', '{bot_id}');
  script.setAttribute('data-name', '{safe_name}');
  document.body.appendChild(script);
}});
&lt;/script&gt;</pre>

                
                <h4>Nuxt.js</h4>
                <p>Add this to your page component or layout:</p>
                <pre class="code-block">&lt;script setup&gt;
import {{ useHead }} from '#head';
useHead({{
  script: [
    {{
      src: 'https://www.upindersangha.com/docative-widget.js',
      async: true,
      'data-bot-id': '{bot_id}',
      'data-name': '{safe_name}',
      tagPosition: 'bodyClose'
    }}
  ],
}})
&lt;/script&gt;</pre>
                
                <h4>React</h4>
                <p>Add this to your component or App.js:</p>
                <pre class="code-block">import React, {{ useEffect }} from 'react';
function App() {{
  useEffect(() => {{
    const script = document.createElement('script');
    script.src = 'https://www.upindersangha.com/docative-widget.js';
    script.async = true;
    script.setAttribute('data-bot-id', '{bot_id}');
    script.setAttribute('data-name', '{safe_name}');
    document.body.appendChild(script);
  }}, []);
  return (&lt;div&gt;Your App Content&lt;/div&gt;);
}}
export default App;</pre>
                
                <h4>Next.js</h4>
                <p>Add this to your page component or layout:</p>
                <pre class="code-block">import Script from 'next/script';

function MyPage() {{
  return (
    &lt;div&gt;
      {{'{{'}}/* Your page content */{{'"}}
      
      &lt;Script
        src="https://www.upindersangha.com/docative-widget.js"
        strategy="afterInteractive"
        data-bot-id="{bot_id}"
        data-name="{safe_name}"
      /&gt;
    &lt;/div&gt;
  );
}}

export default MyPage;</pre>
                
                <h4>Angular</h4>
                <p>Add this to your component:</p>
                <pre class="code-block">import {{ Component, OnInit }} from '@angular/core';
@Component({{
  selector: 'app-your-component',
  template: `&lt;div&gt;Your component content&lt;/div&gt;`
}})
export class YourComponent implements OnInit {{
  ngOnInit() {{
    const script = document.createElement('script');
    script.src = 'https://www.upindersangha.com/docative-widget.js';
    script.async = true;
    script.setAttribute('data-bot-id', '{bot_id}');
    script.setAttribute('data-name', '{safe_name}');
    document.body.appendChild(script);
  }}
}}</pre>
                
                <p>For detailed instructions, check our <a href="https://www.upindersangha.com/docative/user-guide">Integration Guide</a>.</p>
            </div>
            
            <p>If you need help integrating with other platforms or have any questions, feel free to ask the assistant chatbot on our website <a href="https://www.upindersangha.com/docative">https://www.upindersangha.com/docative</a>! It can provide guidance on integration with WordPress, Shopify, Webflow, and more.</p>
            
            <p>We hope you enjoy using Docative! Feel free to create more chatbots for your other documents.</p>
            
            <div style="text-align: center;">
                <a href="https://www.upindersangha.com/docative" class="cta">Create Another Chatbot</a>
            </div>
        </div>
        
        <div class="footer">
            <p>© {datetime.now().year} Docative. All rights reserved.</p>
            <p>This email was sent to {safe_to_email}</p>
        </div>
    </body>
    </html>
    """
    # Plain text content
    plain_text_content = f"""
Hi {safe_name},
Thank you for using Docative! Your custom chatbot is now ready to be embedded on your website.
Your script tag:
{script_tag}
Simply paste this script tag into your website's HTML where you want the chatbot to appear.
For specific platforms, here are the simplest integration methods:
HTML / Static Website:
Paste the script tag just before the closing </body> tag of your HTML file.
Vue.js:
Add this to your page component or app.vue:
<script setup>
import {{ onMounted }} from 'vue';

onMounted(() => {{
  const script = document.createElement('script');
  script.src = 'https://www.upindersangha.com/docative-widget.js';
  script.async = true;
  script.setAttribute('data-bot-id', '{bot_id}');
  script.setAttribute('data-name', '{safe_name}');
  document.body.appendChild(script);
}});
</script>

Nuxt.js:
Add this to your page component or layout:
<script setup>
import {{ useHead }} from '#head';
useHead({{
  script: [
    {{
      src: 'https://www.upindersangha.com/docative-widget.js',
      async: true,
      'data-bot-id': '{bot_id}',
      'data-name': '{safe_name}',
      tagPosition: 'bodyClose'
    }}
  ],
}})
</script>
React:
Add this to your component or App.js:
import React, {{ useEffect }} from 'react';
function App() {{
  useEffect(() => {{
    const script = document.createElement('script');
    script.src = 'https://www.upindersangha.com/docative-widget.js';
    script.async = true;
    script.setAttribute('data-bot-id', '{bot_id}');
    script.setAttribute('data-name', '{safe_name}');
    document.body.appendChild(script);
  }}, []);
  return (&lt;div&gt;Your App Content&lt;/div&gt;);
}}
export default App;
Next.js:
Add this to your page component or layout:
import Script from 'next/script';
function MyPage() {{
  return (
    &lt;div&gt;
      {{'{{'}}/* Your page content */{{'"}}
      &lt;Script
        src="https://www.upindersangha.com/docative-widget.js"
        strategy="afterInteractive"
        data-bot-id="{bot_id}"
        data-name="{safe_name}"
      /&gt;
    &lt;/div&gt;
  );
}}
export default MyPage;
Angular:
Add this to your component:
import {{ Component, OnInit }} from '@angular/core';
@Component({{
  selector: 'app-your-component',
  template: `&lt;div&gt;Your component content&lt;/div&gt;`
}})
export class YourComponent implements OnInit {{
  ngOnInit() {{
    const script = document.createElement('script');
    script.src = 'https://www.upindersangha.com/docative-widget.js';
    script.async = true;
    script.setAttribute('data-bot-id', '{bot_id}');
    script.setAttribute('data-name', '{safe_name}');
    document.body.appendChild(script);
  }}
}}
For detailed instructions, check our Integration Guide: https://www.upindersangha.com/docative/user-guide .
If you need help integrating with other platforms or have any questions, feel free to ask the assistant chatbot on our website https://www.upindersangha.com/docative ! It can provide guidance on integration with WordPress, Shopify, Webflow, and more.
We hope you enjoy using Docative! Feel free to create more chatbots for your other documents.
Best regards,
The Docative Team
https://www.upindersangha.com/docative
    """
    # Attach HTML and plain text parts
    msg.attach(MIMEText(plain_text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    # Send email with error handling
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except smtplib.SMTPException as e:
        raise Exception(f"Failed to send email: {str(e)}") from e