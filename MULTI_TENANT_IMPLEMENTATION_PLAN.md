# Multi-Tenant Implementation Plan for 7cycles-ai

## Overview
This document provides a detailed step-by-step implementation plan for transforming 7cycles-ai into a multi-tenant system with organization and project scoping.

## Implementation Timeline: 9 Weeks

## Week 1-2: Core Infrastructure

### Day 1-2: Database Schema Setup
1. Create Supabase migration files for identity tables
   - [ ] Create `001_create_organizations_table.sql`
   - [ ] Create `002_create_projects_table.sql`
   - [ ] Create `003_create_users_table.sql`
   - [ ] Create `004_create_memberships_tables.sql`
   - [ ] Create `005_create_api_keys_table.sql`
   - [ ] Create `006_create_audit_logs_table.sql`

2. Set up Row-Level Security (RLS) policies
   - [ ] Create RLS policies for organizations
   - [ ] Create RLS policies for projects
   - [ ] Create RLS policies for user data
   - [ ] Create RLS template for agent tables

### Day 3-5: Authentication System
3. Implement JWT authentication
   - [ ] Create `app/core/auth.py` with JWT utilities
   - [ ] Create `app/core/security.py` for password hashing
   - [ ] Create `app/models/auth.py` for auth models
   - [ ] Set up Supabase Auth integration

4. Create authentication endpoints
   - [ ] Create `app/api/routers/auth.py`
   - [ ] Implement `/auth/signup` endpoint
   - [ ] Implement `/auth/login` endpoint
   - [ ] Implement `/auth/refresh` endpoint
   - [ ] Implement `/auth/logout` endpoint

### Day 6-8: Middleware & Dependencies
5. Create context middleware
   - [ ] Create `app/core/middleware.py`
   - [ ] Implement organization/project extraction
   - [ ] Add request context injection
   - [ ] Create permission checking middleware

6. Update dependencies
   - [ ] Update `app/core/dependencies.py`
   - [ ] Create `get_current_user` dependency
   - [ ] Create `get_request_context` dependency
   - [ ] Create `check_permission` dependency

### Day 9-10: Testing Foundation
7. Set up testing infrastructure
   - [ ] Create test utilities for multi-tenant testing
   - [ ] Create fixtures for organizations/users
   - [ ] Write tests for auth endpoints
   - [ ] Write tests for middleware

## Week 3: Storage Layer Updates

### Day 11-12: Scoped Storage Adapter
8. Implement scoped storage
   - [ ] Create `app/core/storage/scoped_adapter.py`
   - [ ] Update storage factory
   - [ ] Add context injection to storage operations
   - [ ] Update Supabase adapter for multi-tenancy

### Day 13-15: Migration Utilities
9. Create data migration tools
   - [ ] Create `scripts/migrate_to_multi_tenant.py`
   - [ ] Create default organization setup
   - [ ] Create data migration functions
   - [ ] Create rollback procedures

## Week 4: Agent Migration - Phase 1

### Day 16-18: Base Agent Updates
10. Update base agent class
    - [ ] Modify `app/agents/crews/base_crew.py`
    - [ ] Add context support to agents
    - [ ] Implement `get_scoped_storage` method
    - [ ] Add backward compatibility mode

### Day 19-20: Pilot Agent Migration
11. Migrate QA Agent
    - [ ] Update `app/agents/qa_agent.py`
    - [ ] Add context to knowledge base queries
    - [ ] Update storage operations
    - [ ] Write comprehensive tests

## Week 5: Agent Migration - Phase 2

### Day 21-25: Migrate Remaining Agents
12. Migrate all agents systematically
    - [ ] Affirmations Agent
    - [ ] Content Strategy Agent
    - [ ] Instagram Poster Agent
    - [ ] Visual Post Creator Agent
    - [ ] Video Generation Agent
    - [ ] All other agents

## Week 6: API Endpoint Updates

### Day 26-28: Core API Updates
13. Add authentication to existing endpoints
    - [ ] Update content generation endpoints
    - [ ] Update affirmations endpoints
    - [ ] Update Instagram endpoints
    - [ ] Update visual posts endpoints

### Day 29-30: New Organization/Project APIs
14. Create organization management APIs
    - [ ] Create `/orgs` endpoints
    - [ ] Create `/projects` endpoints
    - [ ] Create `/members` endpoints
    - [ ] Create API key management endpoints

## Week 7: Frontend Integration

### Day 31-33: Authentication UI
15. Update frontend for authentication
    - [ ] Create login/signup components
    - [ ] Add auth state management
    - [ ] Update API client with auth headers
    - [ ] Add token refresh logic

### Day 34-35: Organization/Project UI
16. Create organization/project selection
    - [ ] Organization switcher component
    - [ ] Project selector component
    - [ ] Update navigation with context
    - [ ] Add member management UI

## Week 8: Data Migration & Testing

### Day 36-37: Production Data Migration
17. Execute data migration
    - [ ] Backup existing data
    - [ ] Run migration scripts
    - [ ] Verify data integrity
    - [ ] Test rollback procedures

### Day 38-40: Integration Testing
18. Comprehensive testing
    - [ ] End-to-end multi-tenant flows
    - [ ] Data isolation testing
    - [ ] Performance testing
    - [ ] Security testing

## Week 9: Deployment & Monitoring

### Day 41-42: Staged Deployment
19. Deploy with feature flags
    - [ ] Deploy to staging environment
    - [ ] Enable for test organizations
    - [ ] Monitor performance metrics
    - [ ] Gather user feedback

### Day 43-45: Production Rollout
20. Full production deployment
    - [ ] Enable for all users
    - [ ] Monitor error rates
    - [ ] Handle support issues
    - [ ] Document lessons learned

## Daily Implementation Checklist

### Before Starting Each Day:
- [ ] Review the day's tasks
- [ ] Check for blockers
- [ ] Update task status in todo list

### During Implementation:
- [ ] Write tests for new code
- [ ] Update documentation
- [ ] Commit changes frequently
- [ ] Test locally before pushing

### End of Day:
- [ ] Update progress in todo list
- [ ] Document any issues
- [ ] Plan next day's tasks
- [ ] Communicate blockers

## Success Criteria

### Technical Success:
- All tests passing
- No data loss during migration
- Performance within acceptable limits
- Security audit passed

### Business Success:
- Zero downtime during migration
- All existing features working
- User satisfaction maintained
- Clear documentation available

## Rollback Plan

If issues arise during implementation:
1. Feature flag to disable multi-tenancy
2. Revert database migrations
3. Restore from backups
4. Roll back code changes
5. Communicate with users

## Next Steps

1. Review this plan with stakeholders
2. Set up monitoring and alerting
3. Create detailed documentation
4. Begin Week 1 implementation