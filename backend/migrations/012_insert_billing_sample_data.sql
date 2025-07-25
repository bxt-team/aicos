-- Insert sample subscription plans
INSERT INTO subscription_plans (id, name, description, price_cents, currency, interval, included_credits, features) VALUES
    (uuid_generate_v4(), 'Starter', 'Perfect for individuals and small teams', 2900, 'usd', 'month', 500, 
     '{"features": ["500 credits/month", "Basic support", "All agent types", "1 project"]}'),
    
    (uuid_generate_v4(), 'Professional', 'For growing businesses', 9900, 'usd', 'month', 2000,
     '{"features": ["2000 credits/month", "Priority support", "All agent types", "5 projects", "API access"]}'),
    
    (uuid_generate_v4(), 'Enterprise', 'For large organizations', 29900, 'usd', 'month', 10000,
     '{"features": ["10000 credits/month", "Dedicated support", "All agent types", "Unlimited projects", "API access", "Custom integrations"]}'),
    
    (uuid_generate_v4(), 'Starter Annual', 'Starter plan billed annually (2 months free)', 29000, 'usd', 'year', 6000,
     '{"features": ["500 credits/month", "Basic support", "All agent types", "1 project", "20% discount"]}'),
    
    (uuid_generate_v4(), 'Professional Annual', 'Professional plan billed annually (2 months free)', 99000, 'usd', 'year', 24000,
     '{"features": ["2000 credits/month", "Priority support", "All agent types", "5 projects", "API access", "20% discount"]}')
ON CONFLICT DO NOTHING;

-- Insert sample credit packages
INSERT INTO credit_packages (id, name, description, credits, price_cents, currency) VALUES
    (uuid_generate_v4(), 'Small Pack', 'Quick top-up for occasional use', 100, 990, 'usd'),
    (uuid_generate_v4(), 'Medium Pack', 'Good value for regular users', 500, 3990, 'usd'),
    (uuid_generate_v4(), 'Large Pack', 'Best value for power users', 2000, 14990, 'usd'),
    (uuid_generate_v4(), 'Jumbo Pack', 'Maximum savings for heavy usage', 5000, 34990, 'usd')
ON CONFLICT DO NOTHING;

-- Update agent action costs with more detailed pricing
UPDATE agent_action_costs SET credit_cost = CASE
    WHEN agent_type = 'ContentAgent' AND action = 'generate_content' THEN 1.0
    WHEN agent_type = 'ContentAgent' AND action = 'generate_instagram_reel' THEN 5.0
    WHEN agent_type = 'VisualPostAgent' AND action = 'create_visual_post' THEN 2.0
    WHEN agent_type = 'VoiceAgent' AND action = 'generate_voice' THEN 2.0
    WHEN agent_type = 'VideoAgent' AND action = 'generate_video' THEN 10.0
    WHEN agent_type = 'ResearchAgent' AND action = 'research_topic' THEN 1.0
    WHEN agent_type = 'QAAgent' AND action = 'answer_question' THEN 0.5
    WHEN agent_type = 'WorkflowAgent' AND action = 'execute_workflow' THEN 3.0
    ELSE credit_cost
END
WHERE agent_type IN ('ContentAgent', 'VisualPostAgent', 'VoiceAgent', 'VideoAgent', 'ResearchAgent', 'QAAgent', 'WorkflowAgent');

-- Add more agent action costs
INSERT INTO agent_action_costs (agent_type, action, credit_cost, description) VALUES
    ('XPostGeneratorAgent', 'generate_post', 1.0, 'Generate X/Twitter post'),
    ('XSchedulerAgent', 'schedule_post', 0.5, 'Schedule X/Twitter post'),
    ('ThreadsAnalysisAgent', 'analyze_trends', 2.0, 'Analyze Threads trends'),
    ('InstagramAnalyzerAgent', 'analyze_profile', 3.0, 'Analyze Instagram profile'),
    ('BackgroundVideoAgent', 'generate_background', 5.0, 'Generate background video'),
    ('AppTestingAgent', 'run_test', 2.0, 'Run automated app test'),
    ('AffirmationsAgent', 'generate_affirmation', 0.5, 'Generate affirmation'),
    ('ImageSearchAgent', 'search_images', 1.0, 'Search for images')
ON CONFLICT (agent_type, action) DO NOTHING;