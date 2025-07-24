'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import Link from 'next/link'

const plans = [
  {
    name: 'Solo Founder',
    price: { monthly: 49, yearly: 490 },
    description: 'Perfect for solo entrepreneurs and indie hackers',
    features: [
      '3 AI Departments',
      'Up to 10 AI agents',
      '5 active projects',
      'Basic analytics dashboard',
      'Email & chat support',
      'All integrations included',
      '14-day free trial',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    name: 'AI-First Team',
    price: { monthly: 199, yearly: 1990 },
    description: 'Ideal for small teams building the future',
    features: [
      '10 AI Departments',
      'Up to 50 AI agents',
      'Unlimited projects',
      'Advanced analytics & KPI tracking',
      'Priority support',
      'Custom agent training',
      'API access',
      'Team collaboration tools',
      'Custom workflows',
    ],
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    name: 'Scale-up',
    price: { monthly: 599, yearly: 5990 },
    description: 'For ambitious companies ready to scale',
    features: [
      'Unlimited AI Departments',
      'Unlimited AI agents',
      'Enterprise analytics',
      'Dedicated success manager',
      'Custom integrations',
      'SLA guarantee',
      'Advanced security features',
      'Multi-organization support',
      'White-label options',
    ],
    cta: 'Contact Sales',
    popular: false,
  },
]

const Pricing = () => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  })

  return (
    <section id="pricing" className="section-padding">
      <div className="max-w-7xl mx-auto container-padding">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold text-secondary-900 mb-4">
            Pricing for{' '}
            <span className="gradient-text">Every Stage</span>
          </h2>
          <p className="text-lg md:text-xl text-secondary-600 max-w-3xl mx-auto mb-8">
            Whether you're a solo founder or scaling team, we have the perfect plan for you.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center p-1 bg-gray-100 rounded-full">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 rounded-full font-medium transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-6 py-2 rounded-full font-medium transition-all ${
                billingCycle === 'yearly'
                  ? 'bg-white text-gray-900 shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Yearly
              <span className="ml-2 text-sm text-green-600">Save 20%</span>
            </button>
          </div>
        </motion.div>

        <div ref={ref} className="grid lg:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className={`relative ${plan.popular ? 'lg:-mt-8' : ''}`}
            >
              {plan.popular && (
                <div className="absolute -top-5 left-0 right-0 flex justify-center">
                  <span className="bg-gradient-to-r from-primary-600 to-secondary-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              <div
                className={`h-full bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden ${
                  plan.popular ? 'ring-2 ring-primary-600' : ''
                }`}
              >
                <div className="p-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-6">{plan.description}</p>

                  <div className="mb-6">
                    {typeof plan.price[billingCycle] === 'number' ? (
                      <>
                        <span className="text-4xl font-bold text-gray-900">
                          ${plan.price[billingCycle]}
                        </span>
                        <span className="text-gray-600">
                          /{billingCycle === 'monthly' ? 'month' : 'year'}
                        </span>
                      </>
                    ) : (
                      <span className="text-3xl font-bold text-gray-900">
                        {plan.price[billingCycle]}
                      </span>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start">
                        <svg
                          className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link
                    href={plan.name === 'Enterprise' ? '/contact' : 'http://localhost:3000/signup'}
                    className={`block w-full text-center py-3 px-6 rounded-full font-semibold transition-all ${
                      plan.popular
                        ? 'bg-gradient-to-r from-primary-600 to-secondary-600 text-white hover:shadow-lg transform hover:scale-105'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* FAQ Link */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center mt-16"
        >
          <p className="text-gray-600">
            Have questions?{' '}
            <Link href="/faq" className="text-primary-600 hover:text-primary-700 font-medium">
              Check our FAQ
            </Link>{' '}
            or{' '}
            <Link href="/contact" className="text-primary-600 hover:text-primary-700 font-medium">
              contact our sales team
            </Link>
          </p>
        </motion.div>
      </div>
    </section>
  )
}

export default Pricing