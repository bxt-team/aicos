'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'

interface WaitlistSignupProps {
  variant?: 'hero' | 'inline'
  className?: string
}

const WaitlistSignup = ({ variant = 'hero', className = '' }: WaitlistSignupProps) => {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!email) return

    setIsSubmitting(true)
    setMessage(null)

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (response.ok) {
        setMessage({ type: 'success', text: 'Thank you! You\'ve been added to our waitlist.' })
        setEmail('')
      } else {
        setMessage({ type: 'error', text: data.error || 'Something went wrong. Please try again.' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to join waitlist. Please try again.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (variant === 'hero') {
    return (
      <motion.div 
        className={`mt-8 ${className}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-secondary-800 mb-2">
            🚀 Launching soon on ProductHunt!
          </h3>
          <p className="text-sm text-secondary-600">
            Be the first to know when we go live and get exclusive early access.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="flex-1 px-6 py-4 bg-white border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-gray-700"
            required
            disabled={isSubmitting}
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-8 py-4 bg-gradient-to-r from-primary-600 to-secondary-600 text-white rounded-full font-semibold hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none whitespace-nowrap"
          >
            {isSubmitting ? 'Joining...' : 'Join Waitlist'}
          </button>
        </form>
        {message && (
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`mt-4 text-sm ${message.type === 'success' ? 'text-green-600' : 'text-red-600'}`}
          >
            {message.text}
          </motion.p>
        )}
      </motion.div>
    )
  }

  return (
    <div className={`bg-gradient-to-r from-primary-50 to-secondary-50 rounded-2xl p-8 ${className}`}>
      <div className="text-center mb-6">
        <span className="inline-flex items-center gap-2 bg-orange-100 text-orange-800 text-sm font-semibold px-4 py-2 rounded-full mb-4">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          ProductHunt Launch Coming Soon
        </span>
        <h3 className="text-2xl font-heading font-bold text-secondary-900 mb-2">
          Be the first to know when we launch!
        </h3>
        <p className="text-secondary-600">
          Join our waitlist and get early access to AI-powered business automation.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="max-w-md mx-auto">
        <div className="flex flex-col gap-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="px-6 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-gray-700"
            required
            disabled={isSubmitting}
          />
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full px-6 py-3 bg-gradient-to-r from-primary-600 to-secondary-600 text-white rounded-lg font-semibold hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isSubmitting ? 'Joining...' : 'Join Waitlist'}
          </button>
        </div>
      </form>
      {message && (
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={`mt-4 text-sm text-center ${message.type === 'success' ? 'text-green-600' : 'text-red-600'}`}
        >
          {message.text}
        </motion.p>
      )}
    </div>
  )
}

export default WaitlistSignup