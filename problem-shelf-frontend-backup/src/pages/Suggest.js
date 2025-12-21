import React, { useState, useEffect } from 'react';
import { Grid } from '@mui/material';
import ProblemCard from '../components/ProblemCard';
import SearchBar from '../components/SearchBar';
import { useLocation } from 'react-router-dom';
import axios from 'axios';

function Suggest() {
  const [problems, setProblems] = useState([]);
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const tech = searchParams.get('tech') || '';

  useEffect(() => {
    if (tech) {
      axios.get(`http://localhost:5000/suggest?tech=${tech}`)
        .then(res => setProblems(res.data));
    }
  }, [tech]);

  return (
    <div>
      <SearchBar />
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

export default Suggest;