import React, { useState } from 'react';
import { TextField, Button, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';

function SearchBar() {
  const [tech, setTech] = useState('');
  const navigate = useNavigate();

  const handleSearch = () => {
    if (tech) navigate(`/suggest?tech=${tech}`);
  };

  return (
    <Grid container spacing={2} justifyContent="center" style={{ padding: '1rem' }}>
      <Grid item>
        <TextField
          label="Enter Tech Stack (e.g., python web)"
          value={tech}
          onChange={(e) => setTech(e.target.value)}
          variant="outlined"
        />
      </Grid>
      <Grid item>
        <Button variant="contained" color="primary" onClick={handleSearch}>
          Search
        </Button>
      </Grid>
    </Grid>
  );
}

export default SearchBar;