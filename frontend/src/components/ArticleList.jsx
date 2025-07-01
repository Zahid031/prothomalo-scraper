import React from 'react';

const ArticleList = ({ articles, loading, error, page, totalPages, setPage }) => {
  return (
    <div className="mt-4">
      <h2>Articles</h2>
      {loading && <p>Loading...</p>}
      {error && <p className="text-danger">{error}</p>}
      <ul className="list-group">
        {articles.map((article) => (
          <li key={article.url} className="list-group-item">
            <h5><a href={article.url} target="_blank" rel="noopener noreferrer">{article.headline}</a></h5>
            <p className="mb-1"><strong>Author:</strong> {article.author}</p>
            <p className="mb-1"><strong>Location:</strong> {article.location}</p>
            <p className="mb-1"><strong>Published:</strong> {new Date(article.published_at).toLocaleString()}</p>
            <p className="mb-1"><strong>Category:</strong> {article.category}</p>
            <p className='mb-1'>
  <strong>Content:</strong> {article.content.slice(0, 300)}...
</p>

          </li>
        ))}
      </ul>
      <div className="d-flex justify-content-center mt-4">
        <button
          className="btn btn-primary me-2"
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button
          className="btn btn-primary ms-2"
          disabled={page >= totalPages}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default ArticleList;