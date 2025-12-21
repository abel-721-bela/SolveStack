import React from 'react';
import { AppBar, Toolbar, Typography, InputBase, Button } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

function Navbar() {
  const navigate = useNavigate();

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" style={{ flexGrow: 1 }}>
          Problem Shelf
        </Typography>
        <InputBase
          placeholder="Search tech stacks..."
          inputProps={{ 'aria-label': 'search' }}
          style={{ color: 'inherit', marginRight: '1rem' }}
          onKeyPress={(e) => {
            if (e.key === 'Enter') navigate(`/suggest?tech=${e.target.value}`);
          }}
        />
        <Button color="inherit" onClick={() => navigate('/suggest')}>
          Suggest
        </Button>
        <Button color="inherit" onClick={() => navigate('/admin')}>
          Admin
        </Button>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;