import React, { useState, useEffect } from 'react';
import ArticleList from './components/ArticleList';
import SearchBar from './components/SearchBar';
import TaskList from './components/TaskList';
import StartScrapingForm from './components/StartScrapingForm';
import { searchArticles, getArticles } from './services/api';

function App() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [activeTab, setActiveTab] = useState('articles');
  const [taskStarted, setTaskStarted] = useState(false);

  const [searchParams, setSearchParams] = useState(null);
  
  const handleSearch = async (params) => {
    const filteredParams = Object.fromEntries(
      Object.entries(params).filter(([_, v]) => v != null && v !== '')
    );
    setSearchParams(filteredParams);
  };

  const handleReload = () => {
    setSearchParams(null);
    setPage(1);
  };

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        setLoading(true);
        const params = searchParams ? { ...searchParams, page } : { page };
        const response = await (searchParams ? searchArticles(params) : getArticles(params));
        setArticles(response.data.results);
        setTotalPages(response.data.total_pages);
        setError(null);
      } catch (err) {
        setError('Error fetching articles.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (activeTab === 'articles') {
      fetchArticles();
    }
  }, [activeTab, page, searchParams]);
  
  const handleTaskStarted = () => {
    setTaskStarted(true);
    setActiveTab('tasks');
  }
  
  return (
    <div className="App">
      <nav className="navbar navbar-dark bg-dark">
        <div className="container-fluid">
          <span className="navbar-brand mb-0 h1">Prothom Alo Scraper</span>
        </div>
      </nav>

      <div className="container-fluid mt-4">
        <ul className="nav nav-tabs">
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'articles' ? 'active' : ''}`}
              onClick={() => setActiveTab('articles')}
            >
              Articles
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'tasks' ? 'active' : ''}`}
              onClick={() => setActiveTab('tasks')}
            >
              Tasks
            </button>
          </li>
        </ul>

        <div className="tab-content mt-4">
          {activeTab === 'articles' && (
            <div>
              <SearchBar onSearch={handleSearch} setPage={setPage} onReload={handleReload} />
              <ArticleList
                articles={articles}
                loading={loading}
                error={error}
                page={page}
                totalPages={totalPages}
                setPage={setPage}
              />
            </div>
          )}
          {activeTab === 'tasks' && (
            <div>
              <StartScrapingForm onTaskStarted={handleTaskStarted} />
              <TaskList key={taskStarted} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
