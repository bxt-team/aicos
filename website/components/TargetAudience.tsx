'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'

const audiences = [
  {
    title: 'Solo Founders',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    description: 'Build and scale your business without hiring. Let AI departments handle marketing, sales, and operations while you focus on vision and growth.',
    benefits: [
      'No hiring costs or management overhead',
      'Instant access to specialized expertise',
      'Scale up or down based on needs'
    ]
  },
  {
    title: 'Small AI-First Teams',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    description: 'Augment your lean team with AI departments. Each team member can lead multiple AI agents, multiplying productivity without expanding headcount.',
    benefits: [
      'Amplify team capabilities 10x',
      'Maintain startup agility',
      'Focus human talent on creative work'
    ]
  },
  {
    title: 'Digital Entrepreneurs',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>
    ),
    description: 'Run multiple online businesses simultaneously. Deploy AI departments across different ventures, managing everything from content to customer service.',
    benefits: [
      'Manage multiple businesses efficiently',
      'Automate repetitive online tasks',
      'Scale without location constraints'
    ]
  }
]

const TargetAudience = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  })

  return (
    <section ref={ref} className="py-20 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto container-padding">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-heading font-bold text-secondary-900 mb-4">
            Built for Modern Business Leaders
          </h2>
          <p className="text-lg text-secondary-600 max-w-3xl mx-auto">
            Whether you're bootstrapping solo or leading a lean team, AICOS gives you the power of a full company 
            without the complexity of traditional hiring and management.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {audiences.map((audience, index) => (
            <motion.div
              key={audience.title}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.2 }}
              className="group"
            >
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 h-full border border-gray-100 hover:border-primary-200">
                <div className="flex items-center justify-center w-16 h-16 bg-primary-100 text-primary-600 rounded-full mb-6 group-hover:bg-primary-600 group-hover:text-white transition-colors duration-300">
                  {audience.icon}
                </div>
                
                <h3 className="text-2xl font-heading font-semibold text-secondary-900 mb-4">
                  {audience.title}
                </h3>
                
                <p className="text-secondary-600 mb-6">
                  {audience.description}
                </p>
                
                <ul className="space-y-3">
                  {audience.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-sm text-secondary-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-12 text-center"
        >
          <p className="text-lg text-secondary-600 mb-6">
            Join thousands of forward-thinking leaders who are building the future of business with AI
          </p>
          <div className="flex flex-wrap justify-center gap-8">
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-primary-600">5,000+</span>
              <span className="text-secondary-600">Active Users</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-primary-600">50M+</span>
              <span className="text-secondary-600">Tasks Automated</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold text-primary-600">98%</span>
              <span className="text-secondary-600">Time Saved</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default TargetAudience