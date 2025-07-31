import { NextRequest, NextResponse } from 'next/server'
import * as brevo from '@getbrevo/brevo'

// Initialize Brevo client
const apiInstance = new brevo.ContactsApi()
apiInstance.authentications['apiKey'].apiKey = process.env.BREVO_API_KEY || ''

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email } = body

    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      )
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      )
    }

    // Check if API key is configured
    if (!process.env.BREVO_API_KEY) {
      console.error('BREVO_API_KEY is not configured')
      return NextResponse.json(
        { error: 'Service temporarily unavailable' },
        { status: 503 }
      )
    }

    // Create contact in Brevo
    const createContact = new brevo.CreateContact()
    createContact.email = email
    createContact.listIds = process.env.BREVO_LIST_ID ? [parseInt(process.env.BREVO_LIST_ID)] : []
    createContact.attributes = {
      SOURCE: 'producthunt_waitlist',
      SIGNUP_DATE: new Date().toISOString()
    }

    try {
      await apiInstance.createContact(createContact)
      
      // Optional: Send welcome email
      if (process.env.BREVO_TEMPLATE_ID) {
        const sendSmtpEmail = new brevo.TransactionalEmailsApi()
        sendSmtpEmail.authentications['apiKey'].apiKey = process.env.BREVO_API_KEY
        
        const emailData = new brevo.SendSmtpEmail()
        emailData.to = [{ email: email }]
        emailData.templateId = parseInt(process.env.BREVO_TEMPLATE_ID)
        
        await sendSmtpEmail.sendTransacEmail(emailData)
      }

      return NextResponse.json(
        { success: true, message: 'Successfully joined waitlist' },
        { status: 200 }
      )
    } catch (brevoError: any) {
      // Handle duplicate email
      if (brevoError.response?.body?.code === 'duplicate_parameter') {
        return NextResponse.json(
          { success: true, message: 'You\'re already on our waitlist!' },
          { status: 200 }
        )
      }
      
      console.error('Brevo API error:', brevoError)
      throw brevoError
    }
  } catch (error) {
    console.error('Waitlist signup error:', error)
    return NextResponse.json(
      { error: 'Failed to join waitlist. Please try again later.' },
      { status: 500 }
    )
  }
}