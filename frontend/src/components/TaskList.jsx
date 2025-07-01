import React, { useState, useEffect } from 'react';
import { getTasks } from '../services/api';

const TaskList = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await getTasks();
      setTasks(response.data);
      setError(null);
    } catch (err) {
      setError('Error fetching tasks.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container-fluid mt-4">
      <h2>Scraping Tasks</h2>
      {loading && <p>Loading...</p>}
      {error && <p className="text-danger">{error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>Task ID</th>
            <th>Category</th>
            <th>Status</th>
            <th>Max Pages</th>
            <th>Total Articles</th>
            <th>Scraped Articles</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.task_id}>
              <td>{task.task_id}</td>
              <td>{task.category}</td>
              <td>{task.status}</td>
              <td>{task.max_pages}</td>
              <td>{task.total_articles}</td>
              <td>{task.scraped_articles}</td>
              <td>{new Date(task.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TaskList;
