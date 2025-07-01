import React, { useState, useEffect } from 'react';
import { getCategories, startScraping } from '../services/api';

const StartScrapingForm = ({ onTaskStarted }) => {
  const [category, setCategory] = useState('');
  const [maxPages, setMaxPages] = useState(2);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await getCategories();
        setCategories(response.data.categories);
        if (response.data.categories.length > 0) {
          setCategory(response.data.categories[0].value);
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };

    fetchCategories();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await startScraping({ category, max_pages: maxPages });
      setError(null);
      onTaskStarted();
    } catch (err) {
      setError('Error starting scraping task.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid mt-4">
      <h2>Start New Scraping Task</h2>
      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col-md-4">
            <label htmlFor="category" className="form-label">Category</label>
            <select
              id="category"
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div className="col-md-4">
            <label htmlFor="maxPages" className="form-label">Max Pages</label>
            <input
              type="number"
              id="maxPages"
              className="form-control"
              min="1"
              max="10"
              value={maxPages}
              onChange={(e) => setMaxPages(parseInt(e.target.value, 10))}
            />
          </div>
          <div className="col-md-4 d-flex align-items-end">
            <button type="submit" className="btn btn-primary w-100" disabled={loading}>
              {loading ? 'Starting...' : 'Start Scraping'}
            </button>
          </div>
        </div>
        {error && <p className="text-danger mt-2">{error}</p>}
      </form>
    </div>
  );
};

export default StartScrapingForm;
