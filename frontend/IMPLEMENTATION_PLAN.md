# Implementation Plan: Dashboard Improvements & Agent Management ✅

## Overview
This plan outlines the implementation of key features to improve the user onboarding experience and agent management functionality in the AICOS platform.

## Tasks

### 1. Getting Started Guide for New Accounts
**Priority:** High
**Location:** Dashboard component

#### Requirements:
- Display a getting started guide on the dashboard for new accounts
- Guide should include steps for:
  1. Creating a project with description
  2. Setting/creating goals
  3. Adding tasks
  4. Setting up a department
  5. Assigning agents to departments

#### Implementation:
- Add state to track if user is new or has completed onboarding
- Create a `GettingStartedGuide` component
- Integrate with Dashboard to show guide when appropriate
- Store onboarding completion status in user preferences

### 2. Department-Agent Assignment
**Priority:** High
**Location:** Department Management component

#### Requirements:
- Allow users to assign agents to departments
- Show which agents are assigned to each department
- Implement assignment/unassignment functionality

#### Implementation:
- Add agent assignment field to department model
- Create API endpoints for agent-department assignment
- Update DepartmentDetail component with agent assignment UI
- Add agent selection dialog/dropdown

### 3. AI Task Generation Button
**Priority:** High
**Location:** TaskManagement component

#### Requirements:
- Add an AI button to generate tasks based on goals
- Button should be visible and accessible
- Generate relevant tasks using AI

#### Implementation:
- Add AI generation button with icon (similar to other AI buttons in the app)
- Create task generation prompt based on selected goal
- Implement API call to generate tasks
- Display generated tasks for user approval before saving

### 4. Remove Back Buttons from Project Sub-pages
**Priority:** Medium
**Location:** All project sub-components

#### Requirements:
- Remove back navigation buttons from project sub-pages
- These pages are accessible via side menu, so back button is redundant

#### Implementation:
- Search for and remove back button implementations in:
  - ProjectDetail
  - ProjectGoals
  - TaskManagement
  - Other project-related components

## File Changes

### New Files:
1. `frontend/src/components/GettingStartedGuide.tsx` - Onboarding guide component
2. `frontend/src/services/taskGenerationService.ts` - AI task generation service

### Modified Files:
1. `frontend/src/components/Dashboard.tsx` - Add getting started guide
2. `frontend/src/components/DepartmentDetail.tsx` - Add agent assignment UI
3. `frontend/src/components/TaskManagement.tsx` - Add AI generation button
4. `frontend/src/components/ProjectDetail.tsx` - Remove back button
5. `frontend/src/components/ProjectGoals.tsx` - Remove back button
6. `backend/app/api/routers/departments.py` - Add agent assignment endpoints
7. `backend/app/api/routers/tasks.py` - Add AI task generation endpoint

## API Endpoints

### New Endpoints:
1. `POST /api/departments/{department_id}/agents` - Assign agents to department
2. `DELETE /api/departments/{department_id}/agents/{agent_id}` - Remove agent from department
3. `POST /api/tasks/generate` - Generate tasks using AI

## Database Changes:
- Add `assigned_agents` field to departments table (JSON array)
- Add `onboarding_completed` field to user preferences

## Implementation Order:
1. ✅ Create implementation plan (completed)
2. ✅ Remove back buttons (completed)
3. ✅ Add AI task generation button (completed)
4. ✅ Implement department-agent assignment (completed)
5. ✅ Create getting started guide (completed)

## Success Criteria:
- ✅ New users see onboarding guide on dashboard
- ✅ Users can assign/unassign agents to departments
- ✅ AI task generation button is visible and functional
- ✅ No back buttons on project sub-pages
- ✅ All features work seamlessly with existing functionality

## Implementation Summary

### 1. Getting Started Guide
- Created `GettingStartedGuide.tsx` component with step-by-step onboarding
- Integrated into `MainDashboard.tsx` with automatic detection of new users
- Tracks completion of each step dynamically
- Collapsible and dismissible interface
- Progress bar showing overall completion

### 2. Department-Agent Assignment
- Feature was already implemented in `DepartmentManagement.tsx`
- Users can click "Manage" button on any department
- Assignment dialog allows selecting members or AI agents
- Available agents include Q&A, Researcher, Content Creator, and social media agents
- Shows member and agent counts for each department

### 3. AI Task Generation
- Updated `TaskManagement.tsx` to make AI button always visible
- Changed from "AI Suggest" to "AI Generate Tasks" for clarity
- Made button more prominent (contained variant, secondary color)
- Added goal selector in dialog when no goal is pre-selected
- Button is disabled only when no goals exist

### 4. Back Button Removal
- Removed back buttons from all project sub-pages:
  - ProjectGoals.tsx
  - ProjectDetail.tsx
  - ProjectKnowledgeBase.tsx
  - ProjectTasks.tsx
  - ProjectRequired.tsx (kept functional back button)
- Navigation now fully handled by side menu