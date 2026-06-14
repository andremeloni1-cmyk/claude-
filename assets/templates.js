// Pre-written email templates, grouped by job status.
// Placeholders available: {{clientName}}, {{jobType}}, {{date}}, {{time}},
// {{location}}, {{price}}, {{businessName}}, {{yourName}}, {{yourEmail}}, {{yourPhone}}

const EMAIL_TEMPLATES = {
  inquiry: [
    {
      id: "inquiry-response",
      name: "Inquiry Response / Check Availability",
      subject: "Re: {{jobType}} Photography on {{date}}",
      body:
`Hi {{clientName}},

Thanks so much for reaching out about {{jobType}} photography on {{date}}!

I'd love to be a part of it. That date is currently available on my calendar, and I'd be happy to send over more details about my packages and pricing.

Could you let me know a bit more about what you're picturing (timing, location, number of people, and any specific shots you're hoping for)? That'll help me put together the best package for you.

Looking forward to hearing from you!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "quote-package",
      name: "Send Quote / Package Details",
      subject: "Photography Packages & Pricing for {{date}}",
      body:
`Hi {{clientName}},

Thanks for the extra details! Here's an overview of what I'd suggest for your {{jobType}} on {{date}}:

- Coverage: [add hours/duration]
- Includes: edited high-resolution gallery, online proofing & download
- Investment: {{price}}

To lock in {{date}}, I require a signed agreement and a deposit to secure the date — after that it's all yours!

Let me know if you have any questions or if you'd like to move forward, and I can send the booking paperwork over right away.

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "booking-follow-up",
      name: "Booking Follow-Up (after quote sent)",
      subject: "Following up — {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

Just following up on the quote I sent over for your {{jobType}} on {{date}}. I wanted to check in and see if you had any questions, or if you're ready to get the date booked.

Spots for {{date}} are filling up, so if you'd like to move forward just let me know and I'll send the booking agreement and deposit details right away.

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

I wanted to send a quick reminder that I'm currently holding {{date}} for your {{jobType}}, but I'm not able to hold it indefinitely as other inquiries are coming in for that date.

If you'd like to confirm the booking, just let me know and I'll get the paperwork and deposit link sent over so we can lock it in.

No worries at all if your plans have changed — just let me know either way!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ],

  booked: [
    {
      id: "booking-confirmation",
      name: "Booking Confirmation",
      subject: "You're Booked! {{jobType}} on {{date}}",
      body:
`Hi {{clientName}},

You're all set! I'm excited to confirm your {{jobType}} session on {{date}} at {{time}}, location: {{location}}.

Here's a quick recap:
- Date: {{date}}
- Time: {{time}}
- Location: {{location}}
- Investment: {{price}}

I'll be in touch closer to the date with any prep details, but in the meantime, feel free to reach out with any questions at all.

Can't wait!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "pre-shoot-details",
      name: "Pre-Shoot Details & Questionnaire",
      subject: "Getting ready for {{date}} — a few details",
      body:
`Hi {{clientName}},

We're getting close to your {{jobType}} on {{date}}! To help things run smoothly, could you send over a few details when you get a chance:

- Any must-have shots or specific people/groups you'd like photographed
- Timeline for the day (if there's a schedule of events)
- Any outfit changes or locations you have in mind
- Best phone number to reach you on the day

Once I have these, I'll put together a shot list and timeline so everything goes off without a hitch.

Talk soon!

Best,
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

Just a quick note to confirm I'll see you tomorrow, {{date}}, at {{time}} at {{location}}.

A few quick reminders:
- Please arrive a few minutes early if possible so we can start on time
- Bring any extra outfits, props, or accessories you'd like included
- Check the weather and dress accordingly if we're outdoors

If anything changes or you need to reach me, just reply to this email or call/text {{yourPhone}}.

Looking forward to it!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "thank-you-next-steps",
      name: "Thank You & Next Steps (post-shoot)",
      subject: "Thank you! Here's what happens next",
      body:
`Hi {{clientName}},

Thank you so much for the {{jobType}} session on {{date}} — it was a pleasure working with you!

Here's what to expect next:
- I'll begin editing your images shortly
- You'll receive a link to your online gallery once it's ready
- From there you can view, download, and order prints/products

I'll be in touch as soon as your gallery is ready. Thanks again, and please don't hesitate to reach out with any questions in the meantime!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ],

  completed: [
    {
      id: "gallery-delivery",
      name: "Gallery Delivery",
      subject: "Your photos are ready! 📸",
      body:
`Hi {{clientName}},

Great news — your gallery from {{date}} is ready!

You can view, download, and order prints/products here: [insert gallery link]

The gallery will be available for [insert amount of time], so be sure to download your favorites. Let me know if you have any trouble accessing anything.

Thanks again for choosing {{businessName}} — I hope you love these as much as I do!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    },
    {
      id: "review-referral",
      name: "Follow-Up: Review & Referral Request",
      subject: "How did everything turn out?",
      body:
`Hi {{clientName}},

I hope you've had a chance to look through your gallery from {{date}} and that you're loving the photos!

If you have a minute, I'd be so grateful if you could leave a quick review — it really helps a small business like mine. [insert review link]

Also, if you know anyone else who might need a photographer, referrals mean the world to me and I always love working with new faces through your recommendation.

Thanks again for trusting me with your {{jobType}}!

Best,
{{yourName}}
{{businessName}}
{{yourEmail}} | {{yourPhone}}`
    }
  ]
};
