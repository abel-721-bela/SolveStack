import React from 'react';
import { Card, CardContent, Typography, CardActions, Button } from '@mui/material';

function ProblemCard({ problem }) {
  return (
    <Card style={{ margin: '1rem', maxWidth: '300px' }}>
      <CardContent>
        <Typography variant="h6">{problem.title}</Typography>
        <Typography variant="body2" color="textSecondary">
          {problem.description.substring(0, 100)}...
        </Typography>
        <Typography variant="body2">Tech: {problem.suggested_tech}</Typography>
        <Typography variant="caption">Source: {problem.source}</Typography>
      </CardContent>
      <CardActions>
        <Button size="small" href={problem.reference_link} target="_blank">
          View Post
        </Button>
      </CardActions>
    </Card>
  );
}

export default ProblemCard;