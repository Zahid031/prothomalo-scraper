import React, { useState, useEffect } from 'react';
import { getCategories } from '../services/api';

const SearchBar = ({ onSearch, setPage, onReload }) => {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [author, setAuthor] = useState('');
  const [location, setLocation] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await getCategories();
        setCategories(response.data.categories);
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };

    fetchCategories();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch({ query, category, author, location, date_from: dateFrom, date_to: dateTo });
    setPage(1);
  };

  const handleReload = () => {
    setQuery('');
    setCategory('');
    setAuthor('');
    setLocation('');
    setDateFrom('');
    setDateTo('');
    onReload();
  };

  return (
    <div className="container mt-4">
      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col-lg-4 col-md-12 mb-2">
            <input
              type="text"
              className="form-control"
              placeholder="Search for articles..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="col-lg-2 col-md-6 mb-2">
            <select
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          <div className="col-lg-2 col-md-6 mb-2">
            <input
              type="text"
              className="form-control"
              placeholder="Author"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
            />
          </div>
          <div className="col-lg-2 col-md-6 mb-2">
            <input
              type="text"
              className="form-control"
              placeholder="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>
        <div className="row mt-2">
          {/* <div className="col-lg-2 col-md-6 mb-2">
            <input
              type="date"
              className="form-control"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="col-lg-2 col-md-6 mb-2">
            <input
              type="date"
              className="form-control"
              value={dateTo}
              onChange={(e) => setDateTo(e.targe.value)}
            />
          </div> */}
          <div className="col-lg-2 col-md-3 mb-2">
            <button type="submit" className="btn btn-primary w-100">Search</button>
          </div>
          <div className="col-lg-2 col-md-3 mb-2">
            <button type="button" className="btn btn-secondary w-100" onClick={handleReload}>Reload</button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default SearchBar;
