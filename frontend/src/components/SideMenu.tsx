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
            {/* System Management Section */}
            <div className="menu-category">
              <h4 className="category-title">System Management</h4>
              <ul className="agents-list">
                <li>
                  <Link
                    to="/"
                    className={`menu-item ${location.pathname === '/' ? 'active' : ''}`}
                    title="Dashboard"
                  >
                    <span className="agent-icon">📊</span>
                    <div className="agent-info">
                      <span className="agent-name">Dashboard</span>
                      <span className="agent-description">Project overview</span>
                    </div>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/general"
                    className={`menu-item ${location.pathname.includes('/organization-settings/general') ? 'active' : ''}`}
                    title="Organization Details"
                  >
                    <span className="agent-icon">🏢</span>
                    <div className="agent-info">
                      <span className="agent-name">Organization</span>
                      <span className="agent-description">Company details</span>
                    </div>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/members"
                    className={`menu-item ${location.pathname.includes('/organization-settings/members') ? 'active' : ''}`}
                    title="Team Members"
                  >
                    <span className="agent-icon">👥</span>
                    <div className="agent-info">
                      <span className="agent-name">Team</span>
                      <span className="agent-description">Members & roles</span>
                    </div>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/departments"
                    className={`menu-item ${location.pathname.includes('/organization-settings/departments') ? 'active' : ''}`}
                    title="Departments"
                  >
                    <span className="agent-icon">🏗️</span>
                    <div className="agent-info">
                      <span className="agent-name">Departments</span>
                      <span className="agent-description">Manage departments</span>
                    </div>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/organization-settings/billing"
                    className={`menu-item ${location.pathname.includes('/organization-settings/billing') ? 'active' : ''}`}
                    title="Billing"
                  >
                    <span className="agent-icon">💳</span>
                    <div className="agent-info">
                      <span className="agent-name">Billing</span>
                      <span className="agent-description">Credits & usage</span>
                    </div>
                  </Link>
                </li>
              </ul>
            </div>

            {/* Projects Section */}
            <div className="menu-category">
              <h4 
                className="category-title" 
                style={{ cursor: 'pointer' }} 
                onClick={() => setShowProjects(!showProjects)}
              >
                Projects {showProjects ? '▼' : '▶'}
              </h4>
              {showProjects && (
                <ul className="agents-list">
                  {projects.map(project => (
                    <li key={project.id}>
                      <div>
                        <div
                          className={`menu-item ${currentProject?.id === project.id ? 'active' : ''}`}
                          style={{ cursor: 'pointer' }}
                          onClick={() => {
                            setCurrentProject(project);
                            toggleProjectExpansion(project.id);
                          }}
                        >
                          <span 
                            className="agent-icon" 
                            style={{ cursor: 'pointer' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleProjectExpansion(project.id);
                            }}
                          >
                            {expandedProjects.has(project.id) ? '▼' : '▶'}
                          </span>
                          <div className="agent-info">
                            <span className="agent-name">{project.name}</span>
                            <span className="agent-description">{project.description || 'Project workspace'}</span>
                          </div>
                        </div>
                        {expandedProjects.has(project.id) && (
                          <ul className="agents-list" style={{ marginLeft: '20px' }}>
                            <li>
                              <Link
                                to={`/projects/${project.id}`}
                                className={`menu-item ${location.pathname === `/projects/${project.id}` ? 'active' : ''}`}
                                title="Overview"
                              >
                                <span className="agent-icon">📋</span>
                                <div className="agent-info">
                                  <span className="agent-name">Overview</span>
                                  <span className="agent-description">Project details</span>
                                </div>
                              </Link>
                            </li>
                            <li>
                              <Link
                                to={`/projects/${project.id}/knowledgebase`}
                                className={`menu-item ${location.pathname === `/projects/${project.id}/knowledgebase` ? 'active' : ''}`}
                                title="Knowledgebase"
                              >
                                <span className="agent-icon">📚</span>
                                <div className="agent-info">
                                  <span className="agent-name">Knowledgebase</span>
                                  <span className="agent-description">Documents & resources</span>
                                </div>
                              </Link>
                            </li>
                            <li>
                              <Link
                                to={`/projects/${project.id}/tasks`}
                                className={`menu-item ${location.pathname === `/projects/${project.id}/tasks` ? 'active' : ''}`}
                                title="Tasks"
                              >
                                <span className="agent-icon">✅</span>
                                <div className="agent-info">
                                  <span className="agent-name">Tasks</span>
                                  <span className="agent-description">Project tasks</span>
                                </div>
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
                      className={`menu-item ${location.pathname.includes('/organization-settings/projects') ? 'active' : ''}`}
                      title="Manage Projects"
                    >
                      <span className="agent-icon">➕</span>
                      <div className="agent-info">
                        <span className="agent-name">Manage Projects</span>
                        <span className="agent-description">Create & manage</span>
                      </div>
                    </Link>
                  </li>
                </ul>
              )}
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
          </ul>
        )}
      </nav>
    </aside>
    </>
  );
};

export default SideMenu;