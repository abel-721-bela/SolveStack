import React, { useState } from 'react';
import { Button, LinearProgress } from '@mui/material';
import axios from 'axios';

function AdminPanel() {
  const [loading, setLoading] = useState(false);

  const handleScrape = async () => {
    setLoading(true);
    try {
      await axios.post('http://localhost:5000/scrape');
      alert('Scraping completed!');
    } catch (error) {
      alert('Error during scraping');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '2rem' }}>
      <Button variant="contained" color="secondary" onClick={handleScrape} disabled={loading}>
        Trigger Scraping
      </Button>
      {loading && <LinearProgress style={{ marginTop: '1rem' }} />}
    </div>
  );
}

export default AdminPanel;