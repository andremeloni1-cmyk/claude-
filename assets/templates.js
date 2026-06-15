// Pre-written email templates, grouped by job status.
// Placeholders available: {{clientName}}, {{jobType}}, {{date}}, {{time}},
// {{location}}, {{price}}, {{businessName}}, {{yourName}}, {{yourEmail}}, {{yourPhone}}

const EMAIL_TEMPLATES = {
  inquiry: [
    {
      id: "inquiry-response",
      name: "Inquiry Response / Check Availability",
      subject: "Re: {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

Thanks for reaching out about your {{jobType}} — I'd be glad to help.

{{date}} is currently available on my schedule. To put together an accurate quote, could you let me know a few details:

- The site address and best access instructions
- The scope of work (cabinetry layout, finishes, and any plans or measurements you have)
- Your preferred timeframe or any deadlines

Once I have these, I'll get a quote over to you.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "send-quote",
      name: "Send Quote",
      subject: "Quote for your {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

Thanks for the details! Here's a quote for your {{jobType}} on {{date}}:

- Scope: [add scope of work]
- Materials/finishes: [add details]
- Total price: {{price}}

To lock in {{date}}, I'll need a signed confirmation and a deposit to secure the date and order materials.

Let me know if you have any questions or you'd like to go ahead, and I'll send the booking details over.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "quote-follow-up",
      name: "Quote Follow-Up",
      subject: "Following up — quote for {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

Just following up on the quote I sent for your {{jobType}} on {{date}}. Wanted to check in and see if you had any questions, or if you're ready to lock in the date.

{{date}} is filling up, so if you'd like to go ahead just let me know and I'll get the booking confirmed and materials ordered.

Happy to help with anything else in the meantime!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "date-hold-reminder",
      name: "Tentative Date Hold Reminder",
      subject: "Quick reminder — your hold on {{date}}",
      body:
`Hi {{clientName}},

Just a quick reminder that I'm currently holding {{date}} for your {{jobType}}, but I can't hold it indefinitely as other jobs are coming in for that date.

If you'd like to confirm, let me know and I'll send the booking details and deposit info so we can lock it in.

No worries if your plans have changed — just let me know either way!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ],

  booked: [
    {
      id: "booking-confirmation",
      name: "Install Confirmation",
      subject: "Confirmed: {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

You're all set! I'm confirming your {{jobType}} on {{date}} at {{time}}, at {{location}}.

Here's a quick recap:
- Date: {{date}}
- Start time: {{time}}
- Site address: {{location}}
- Total price: {{price}}

I'll be in touch closer to the date to confirm site access details. In the meantime, feel free to reach out with any questions.

Thanks again,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "pre-install-details",
      name: "Pre-Install Details & Site Access",
      subject: "Getting ready for {{date}} — a few details",
      body:
`Hi {{clientName}},

We're getting close to your {{jobType}} on {{date}}! To make sure everything goes smoothly, could you let me know:

- How I'll access the site (keys, gate/alarm codes, or will someone be home)
- Where I can park and bring in materials/tools
- Power and water access on site
- Anything else I should know before I arrive

Once I have these, I'll confirm the schedule for the day.

Talk soon,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "day-before-reminder",
      name: "Day-Before Reminder",
      subject: "See you tomorrow! {{date}} at {{time}}",
      body:
`Hi {{clientName}},

Just confirming I'll be on site tomorrow, {{date}}, from {{time}} at {{location}} for your {{jobType}}.

A couple of reminders:
- Please make sure the area is clear so I can get started on time
- Let me know if access details have changed since we last spoke

If anything comes up, just reply to this email or call/text {{yourPhone}}.

See you then,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "thank-you-next-steps",
      name: "Thank You & Next Steps (post-install)",
      subject: "Thanks for the opportunity — what's next",
      body:
`Hi {{clientName}},

Thank you for trusting me with your {{jobType}} on {{date}} — it was great working with you!

Here's what to expect next:
- I'll send through the final invoice ({{price}}) shortly
- Once payment is received, I'll follow up with any care and maintenance notes for your new joinery

Thanks again, and please don't hesitate to reach out with any questions in the meantime!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ],

  completed: [
    {
      id: "job-complete-invoice",
      name: "Job Complete & Invoice",
      subject: "Your {{jobType}} is complete — invoice attached",
      body:
`Hi {{clientName}},

Great news — your {{jobType}} from {{date}} is now complete!

Total due: {{price}}
[Attach or link to invoice/payment details]

A few care notes for your new joinery:
- [add cleaning/maintenance tips]

Thanks again for choosing {{businessName}} — it was a pleasure working on your home.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "review-referral",
      name: "Follow-Up: Review & Referral Request",
      subject: "How's everything looking?",
      body:
`Hi {{clientName}},

I hope you're loving your new {{jobType}} from {{date}}!

If you have a minute, I'd really appreciate a quick review — it helps a lot. [insert review link]

And if you know anyone else who needs cabinetry or joinery work, I'd love an introduction — referrals mean the world to a small business like mine.

Thanks again for trusting me with your project!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ]
};

// Auto-drafted replies sent back to referral sources when a job from one
// of their inquiry emails is accepted. Keyed by the referral source's
// email address (lowercase). Drafted as a reply in the original thread.
const REFERRAL_REPLY_TEMPLATES = {
  "emily@miikitchen.com.au": {
    body:
`Hi Emily,

Thanks for sending this one through! I've accepted the job for {{clientName}}'s {{jobType}} — it's now booked in for {{date}} at {{location}}.

I'll be in touch with {{clientName}} directly to confirm the details. Thanks again for thinking of me, and please keep them coming!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
  },

  "service@harringtonkitchens.com.au": {
    body:
`Hi team,

Thanks for the referral! I've accepted the job for {{clientName}}'s {{jobType}} — it's now booked in for {{date}} at {{location}}.

I'll be in touch with {{clientName}} directly to arrange the details. Really appreciate you thinking of me for this one.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
  },

  "peter.baldwin@ingenuityjoinery.com": {
    body:
`Hi Peter,

Thanks for passing this one on! I've accepted the job for {{clientName}}'s {{jobType}} — it's booked in for {{date}} at {{location}}.

I'll get in touch with {{clientName}} directly to sort out the details. Appreciate the referral as always.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
  },
};
