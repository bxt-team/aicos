import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useMenu } from '../contexts/MenuContext';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useProject } from '../contexts/ProjectContext';
import './SideMenu.css';

const SideMenu: React.FC = () => {
  const { isMenuOpen: isExpanded, toggleMenu, isMobile } = useMenu();
  const location = useLocation();
  const { user, loading } = useSupabaseAuth();
  const { 
    currentOrganization, 
    organizations,
    loading: orgLoading
  } = useOrganization();
  const { currentProject, projects, setCurrentProject } = useProject();
  const [showProjects, setShowProjects] = useState(true);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());

  // Auto-expand current project
  useEffect(() => {
    if (currentProject?.id && !expandedProjects.has(currentProject.id)) {
      setExpandedProjects(prev => new Set(prev).add(currentProject.id));
    }
  }, [currentProject]);

  // Check URL on mount and expand project if in project route
  useEffect(() => {
    const pathMatch = location.pathname.match(/\/projects\/([^\/]+)/);
    if (pathMatch) {
      const projectId = pathMatch[1];
      setExpandedProjects(prev => new Set(prev).add(projectId));
    }
  }, []);

  // Close menu on route change for mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Prevent body scroll when menu is open on mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobile, isExpanded]);

  const handleOverlayClick = () => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
  };


  const handleToggleClick = () => {
    toggleMenu();
  };

  const toggleProjectExpansion = (projectId: string) => {
    setExpandedProjects(prev => {
      const newSet = new Set(prev);
      if (newSet.has(projectId)) {
        newSet.delete(projectId);
      } else {
        newSet.add(projectId);
      }
      return newSet;
    });
  };


  // Don't render agent menu if no organization exists (after loading is complete)
  // The OnboardingCheck component will handle showing the onboarding wizard
  if (!loading && !orgLoading && user && organizations.length === 0) {
    return null;
  }

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && isExpanded && (
        <div className="menu-overlay" onClick={handleOverlayClick} />
      )}
      
      <aside className={`side-menu ${isExpanded ? 'expanded' : 'collapsed'} ${isMobile ? 'mobile' : ''}`}>
      <div className="side-menu-header">
        <button 
          className="menu-toggle"
          onClick={handleToggleClick}
          aria-label={isExpanded ? 'Collapse menu' : 'Expand menu'}
        >
          {isExpanded ? '◀' : '▶'}
        </button>
        {isExpanded && (
          <div className="menu-title">
            <h3>Navigation</h3>
            {isMobile && (
              <button 
                className="menu-close"
                onClick={handleToggleClick}
                aria-label="Close menu"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>


      <nav className="side-menu-nav">
        {isExpanded ? (
          <>
            {/* Projects Section */}
            <div className="nav-section">
              <div className="section-header">
                <span className="section-title">Projects</span>
                <button className="section-action">⋯</button>
              </div>
              <ul className="nav-list">
                {projects.map(project => (
                  <li key={project.id}>
                    <div>
                      <div
                        className={`nav-item expandable ${currentProject?.id === project.id ? 'active' : ''}`}
                        onClick={() => {
                          setCurrentProject(project);
                          // Only toggle expansion if it's not the current project being clicked
                          if (currentProject?.id !== project.id) {
                            setExpandedProjects(prev => new Set(prev).add(project.id));
                          }
                        }}
                      >
                        <span 
                          className="expand-icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleProjectExpansion(project.id);
                          }}
                        >
                          {expandedProjects.has(project.id) ? '▼' : '▶'}
                        </span>
                        <span className="nav-icon">📁</span>
                        <span className="nav-text">{project.name}</span>
                      </div>
                      {expandedProjects.has(project.id) && (
                        <ul className="sub-list">
                          <li>
                            <Link
                              to={`/projects/${project.id}`}
                              className={`nav-item sub-item ${location.pathname === `/projects/${project.id}` ? 'active' : ''}`}
                              title="Overview"
                            >
                              <span className="nav-icon">📋</span>
                              <span className="nav-text">Overview</span>
                            </Link>
                          </li>
                          <li>
                            <Link
                              to={`/projects/${project.id}/goals`}
                              className={`nav-item sub-item ${location.pathname === `/projects/${project.id}/goals` ? 'active' : ''}`}
                              title="Goals"
                            >
                              <span className="nav-icon">🎯</span>
                              <span className="nav-text">Goals</span>
                            </Link>
                          </li>
                          <li>
                            <Link
                              to={`/projects/${project.id}/tasks`}
                              className={`nav-item sub-item ${location.pathname === `/projects/${project.id}/tasks` ? 'active' : ''}`}
                              title="Tasks"
                            >
                              <span className="nav-icon">✅</span>
                              <span className="nav-text">Tasks</span>
                            </Link>
                          </li>
                          <li>
                            <Link
                              to={`/projects/${project.id}/knowledgebase`}
                              className={`nav-item sub-item ${location.pathname === `/projects/${project.id}/knowledgebase` ? 'active' : ''}`}
                              title="Knowledgebase"
                            >
                              <span className="nav-icon">📚</span>
                              <span className="nav-text">Knowledgebase</span>
                            </Link>
                          </li>
                        </ul>
                      )}
                    </div>
                  </li>
                ))}
                <li>
                  <Link
                    to="/organization-settings/projects"
                    className={`nav-item ${location.pathname.includes('/organization-settings/projects') ? 'active' : ''}`}
                    title="Manage Projects"
                  >
                    <span className="nav-icon">➕</span>
                    <span className="nav-text">Manage Projects</span>
                  </Link>
                </li>
              </ul>
            </div>

            {/* System Management Section */}
            <div className="nav-section">
              <div className="section-header">
                <span className="section-title">System Management</span>
                <button className="section-action">⋯</button>
              </div>
              <ul className="nav-list">
                <li>
                  <Link
                    to="/"
                    className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}
                    title="Dashboard"
                  >
                    <span className="nav-icon">📊</span>
                    <span className="nav-text">Dashboard</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/general"
                    className={`nav-item ${location.pathname.includes('/organization-settings/general') ? 'active' : ''}`}
                    title="Organization Details"
                  >
                    <span className="nav-icon">🏢</span>
                    <span className="nav-text">Organization</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/members"
                    className={`nav-item ${location.pathname.includes('/organization-settings/members') ? 'active' : ''}`}
                    title="Team Members"
                  >
                    <span className="nav-icon">👥</span>
                    <span className="nav-text">Team</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/departments"
                    className={`nav-item ${location.pathname.includes('/organization-settings/departments') ? 'active' : ''}`}
                    title="Departments"
                  >
                    <span className="nav-icon">🏗️</span>
                    <span className="nav-text">Departments</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/billing"
                    className={`nav-item ${location.pathname.includes('/organization-settings/billing') ? 'active' : ''}`}
                    title="Billing"
                  >
                    <span className="nav-icon">💳</span>
                    <span className="nav-text">Billing</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/agent-dashboard"
                    className={`nav-item ${location.pathname === '/agent-dashboard' ? 'active' : ''}`}
                    title="Agents"
                  >
                    <span className="nav-icon">🤖</span>
                    <span className="nav-text">Agents</span>
                  </Link>
                </li>
              </ul>
            </div>
          </>
        ) : (
          <ul className="agents-list-collapsed">
            {/* Collapsed view - show important system items first */}
            <li>
              <Link
                to="/"
                className={`menu-item-collapsed ${location.pathname === '/' ? 'active' : ''}`}
                title="Dashboard"
              >
                <span className="agent-icon">📊</span>
              </Link>
            </li>
            <li>
              <Link
                to="/organization-settings/general"
                className={`menu-item-collapsed ${location.pathname.includes('/organization-settings') ? 'active' : ''}`}
                title="Organization"
              >
                <span className="agent-icon">🏢</span>
              </Link>
            </li>
            <li>
              <Link
                to="/organization-settings/billing"
                className={`menu-item-collapsed ${location.pathname.includes('/billing') ? 'active' : ''}`}
                title="Billing"
              >
                <span className="agent-icon">💳</span>
              </Link>
            </li>
            <li>
              <Link
                to="/agent-dashboard"
                className={`menu-item-collapsed ${location.pathname === '/agent-dashboard' ? 'active' : ''}`}
                title="Agents"
              >
                <span className="agent-icon">🤖</span>
              </Link>
            </li>
          </ul>
        )}
      </nav>
    </aside>
    </>
  );
};

export default SideMenu;