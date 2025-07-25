-- Create billing and credits system tables

-- Customer billing information linked to Stripe
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE,
    default_payment_method_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id)
);

-- Subscription plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stripe_product_id TEXT UNIQUE,
    stripe_price_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    interval TEXT NOT NULL CHECK (interval IN ('month', 'year')),
    included_credits INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    features JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Active subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete')),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credit packages for one-time purchases
CREATE TABLE IF NOT EXISTS credit_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stripe_product_id TEXT UNIQUE,
    stripe_price_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    credits INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Credit balances per organization
CREATE TABLE IF NOT EXISTS credit_balances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    available_credits DECIMAL(10, 2) NOT NULL DEFAULT 0,
    reserved_credits DECIMAL(10, 2) NOT NULL DEFAULT 0,
    total_purchased DECIMAL(10, 2) NOT NULL DEFAULT 0,
    total_consumed DECIMAL(10, 2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id),
    CHECK (available_credits >= 0),
    CHECK (reserved_credits >= 0)
);

-- Credit transactions (purchases, consumption, refunds)
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('purchase', 'subscription_grant', 'consumption', 'refund', 'bonus', 'adjustment')),
    amount DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    stripe_payment_intent_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Credit usage tracking per agent/project
CREATE TABLE IF NOT EXISTS credit_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    agent_type TEXT NOT NULL,
    action TEXT NOT NULL,
    credits_consumed DECIMAL(10, 2) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES users(id)
);

-- Department credit limits
CREATE TABLE IF NOT EXISTS department_credit_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    monthly_limit DECIMAL(10, 2),
    daily_limit DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department_id)
);

-- Payment history
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    stripe_payment_intent_id TEXT UNIQUE,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    stripe_invoice_id TEXT UNIQUE,
    invoice_number TEXT,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    invoice_pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent action credit costs
CREATE TABLE IF NOT EXISTS agent_action_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type TEXT NOT NULL,
    action TEXT NOT NULL,
    credit_cost DECIMAL(10, 2) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_type, action)
);

-- Create indexes for performance
CREATE INDEX idx_credit_usage_org_created ON credit_usage(organization_id, created_at DESC);
CREATE INDEX idx_credit_usage_project ON credit_usage(project_id, created_at DESC);
CREATE INDEX idx_credit_usage_department ON credit_usage(department_id, created_at DESC);
CREATE INDEX idx_credit_transactions_org ON credit_transactions(organization_id, created_at DESC);
CREATE INDEX idx_payments_customer ON payments(customer_id, created_at DESC);
CREATE INDEX idx_invoices_customer ON invoices(customer_id, created_at DESC);

-- RLS Policies
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE department_credit_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- Customers: viewable by organization members
CREATE POLICY "customers_view_policy" ON customers
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Subscriptions: viewable by organization members
CREATE POLICY "subscriptions_view_policy" ON subscriptions
    FOR SELECT USING (
        customer_id IN (
            SELECT id FROM customers 
            WHERE organization_id IN (
                SELECT organization_id FROM organization_members 
                WHERE user_id = auth.uid()
            )
        )
    );

-- Credit balances: viewable by organization members
CREATE POLICY "credit_balances_view_policy" ON credit_balances
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Credit transactions: viewable by organization members
CREATE POLICY "credit_transactions_view_policy" ON credit_transactions
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Credit usage: viewable by organization members
CREATE POLICY "credit_usage_view_policy" ON credit_usage
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Department credit limits: viewable by organization members
CREATE POLICY "department_credit_limits_view_policy" ON department_credit_limits
    FOR SELECT USING (
        department_id IN (
            SELECT id FROM departments 
            WHERE organization_id IN (
                SELECT organization_id FROM organization_members 
                WHERE user_id = auth.uid()
            )
        )
    );

-- Payments: viewable by organization members
CREATE POLICY "payments_view_policy" ON payments
    FOR SELECT USING (
        customer_id IN (
            SELECT id FROM customers 
            WHERE organization_id IN (
                SELECT organization_id FROM organization_members 
                WHERE user_id = auth.uid()
            )
        )
    );

-- Invoices: viewable by organization members
CREATE POLICY "invoices_view_policy" ON invoices
    FOR SELECT USING (
        customer_id IN (
            SELECT id FROM customers 
            WHERE organization_id IN (
                SELECT organization_id FROM organization_members 
                WHERE user_id = auth.uid()
            )
        )
    );

-- Functions for credit operations
CREATE OR REPLACE FUNCTION consume_credits(
    p_organization_id UUID,
    p_amount DECIMAL,
    p_project_id UUID DEFAULT NULL,
    p_department_id UUID DEFAULT NULL,
    p_agent_type TEXT DEFAULT NULL,
    p_action TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_balance DECIMAL;
    v_new_balance DECIMAL;
BEGIN
    -- Lock the balance row
    SELECT available_credits INTO v_current_balance
    FROM credit_balances
    WHERE organization_id = p_organization_id
    FOR UPDATE;
    
    -- Check if sufficient credits
    IF v_current_balance < p_amount THEN
        RETURN FALSE;
    END IF;
    
    -- Update balance
    v_new_balance := v_current_balance - p_amount;
    UPDATE credit_balances
    SET available_credits = v_new_balance,
        total_consumed = total_consumed + p_amount,
        updated_at = NOW()
    WHERE organization_id = p_organization_id;
    
    -- Record transaction
    INSERT INTO credit_transactions (
        organization_id, type, amount, balance_after, 
        description, metadata
    ) VALUES (
        p_organization_id, 'consumption', -p_amount, v_new_balance,
        COALESCE(p_agent_type || ' - ' || p_action, 'Credit consumption'),
        p_metadata
    );
    
    -- Record usage details
    IF p_agent_type IS NOT NULL THEN
        INSERT INTO credit_usage (
            organization_id, project_id, department_id,
            agent_type, action, credits_consumed, metadata
        ) VALUES (
            p_organization_id, p_project_id, p_department_id,
            p_agent_type, COALESCE(p_action, 'unknown'), p_amount, p_metadata
        );
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add credits
CREATE OR REPLACE FUNCTION add_credits(
    p_organization_id UUID,
    p_amount DECIMAL,
    p_type TEXT,
    p_description TEXT DEFAULT NULL,
    p_stripe_payment_intent_id TEXT DEFAULT NULL
) RETURNS DECIMAL AS $$
DECLARE
    v_new_balance DECIMAL;
BEGIN
    -- Update balance
    UPDATE credit_balances
    SET available_credits = available_credits + p_amount,
        total_purchased = CASE 
            WHEN p_type IN ('purchase', 'subscription_grant') 
            THEN total_purchased + p_amount 
            ELSE total_purchased 
        END,
        updated_at = NOW()
    WHERE organization_id = p_organization_id
    RETURNING available_credits INTO v_new_balance;
    
    -- If no balance exists, create one
    IF v_new_balance IS NULL THEN
        INSERT INTO credit_balances (
            organization_id, available_credits, total_purchased
        ) VALUES (
            p_organization_id, p_amount, 
            CASE WHEN p_type IN ('purchase', 'subscription_grant') THEN p_amount ELSE 0 END
        )
        RETURNING available_credits INTO v_new_balance;
    END IF;
    
    -- Record transaction
    INSERT INTO credit_transactions (
        organization_id, type, amount, balance_after,
        description, stripe_payment_intent_id
    ) VALUES (
        p_organization_id, p_type, p_amount, v_new_balance,
        p_description, p_stripe_payment_intent_id
    );
    
    RETURN v_new_balance;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_department_credit_limits_updated_at BEFORE UPDATE ON department_credit_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_agent_action_costs_updated_at BEFORE UPDATE ON agent_action_costs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Insert default agent action costs
INSERT INTO agent_action_costs (agent_type, action, credit_cost, description) VALUES
    ('ContentAgent', 'generate_content', 1.0, 'Generate text content'),
    ('ContentAgent', 'generate_instagram_reel', 5.0, 'Generate Instagram Reel video'),
    ('VisualPostAgent', 'create_visual_post', 2.0, 'Create visual post with images'),
    ('VoiceAgent', 'generate_voice', 2.0, 'Generate voice audio'),
    ('VideoAgent', 'generate_video', 10.0, 'Generate video content'),
    ('ResearchAgent', 'research_topic', 1.0, 'Research a topic'),
    ('QAAgent', 'answer_question', 0.5, 'Answer a question'),
    ('WorkflowAgent', 'execute_workflow', 3.0, 'Execute workflow')
ON CONFLICT (agent_type, action) DO NOTHING;

-- Grant new user signup bonus credits
CREATE OR REPLACE FUNCTION grant_signup_bonus()
RETURNS TRIGGER AS $$
BEGIN
    -- Grant 100 free credits to new organizations
    PERFORM add_credits(
        NEW.id, 
        100.0, 
        'bonus', 
        'Welcome bonus credits'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER grant_signup_bonus_trigger
    AFTER INSERT ON organizations
    FOR EACH ROW EXECUTE FUNCTION grant_signup_bonus();