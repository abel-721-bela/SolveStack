import React, { useState, useEffect } from 'react';
import { Grid } from '@mui/material';
import ProblemCard from '../components/ProblemCard';
import axios from 'axios';

function Dashboard() {
  const [problems, setProblems] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/problems')
      .then(res => setProblems(res.data))
      .catch(err => console.error('Error fetching problems:', err));
  }, []);

  return (
    <div>
      <Grid container spacing={3} justifyContent="center">
        {problems.map((problem, index) => (
          <Grid item key={index}>
            <ProblemCard problem={problem} />
          </Grid>
        ))}
      </Grid>
    </div>
  );
}

export default Dashboard;