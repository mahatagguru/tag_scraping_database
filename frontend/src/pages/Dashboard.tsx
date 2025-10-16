import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Category as CategoryIcon,
  CalendarToday as YearIcon,
  CardGiftcard as SetIcon,
  CardGiftcard as CardIcon,
  Grade as GradeIcon,
  Timeline as PopulationIcon,
  Schedule as TimeIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getDashboardStats } from '../services/api';
import { format } from 'date-fns';

const StatCard: React.FC<{
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}> = ({ title, value, icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: '50%',
            p: 1,
            mr: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </Box>
        <Box>
          <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
            {value.toLocaleString()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const ActivityItem: React.FC<{
  level: string;
  message: string;
  timestamp: string;
  component?: string;
  operation?: string;
  status?: string;
}> = ({ level, message, timestamp, component, operation, status }) => {
  const getIcon = () => {
    switch (level) {
      case 'ERROR':
        return <ErrorIcon color="error" />;
      case 'WARNING':
        return <WarningIcon color="warning" />;
      case 'SUCCESS':
        return <SuccessIcon color="success" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'SUCCESS':
        return 'success';
      case 'FAILURE':
        return 'error';
      case 'PARTIAL':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <ListItem>
      <ListItemIcon>{getIcon()}</ListItemIcon>
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Typography variant="body2">{message}</Typography>
            {status && (
              <Chip
                label={status}
                size="small"
                color={getStatusColor() as any}
                variant="outlined"
              />
            )}
          </Box>
        }
        secondary={
          <Box>
            <Typography variant="caption" color="text.secondary">
              {format(new Date(timestamp), 'MMM dd, yyyy HH:mm:ss')}
            </Typography>
            {component && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                • {component}
              </Typography>
            )}
            {operation && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                • {operation}
              </Typography>
            )}
          </Box>
        }
      />
    </ListItem>
  );
};

const Dashboard: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery(
    'dashboard-stats',
    getDashboardStats,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load dashboard data. Please check your connection and try again.
      </Alert>
    );
  }

  if (!stats) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No data available. The database appears to be empty. Run the scraping pipeline to populate data.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3 }}>
        Dashboard Overview
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Categories"
            value={stats.total_categories}
            icon={<CategoryIcon sx={{ color: 'white' }} />}
            color="#1976d2"
            subtitle="Sports"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Years"
            value={stats.total_years}
            icon={<YearIcon sx={{ color: 'white' }} />}
            color="#388e3c"
            subtitle="Seasons"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Sets"
            value={stats.total_sets}
            icon={<SetIcon sx={{ color: 'white' }} />}
            color="#f57c00"
            subtitle="Collections"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Cards"
            value={stats.total_cards}
            icon={<CardIcon sx={{ color: 'white' }} />}
            color="#7b1fa2"
            subtitle="Individual Cards"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Grades"
            value={stats.total_grades}
            icon={<GradeIcon sx={{ color: 'white' }} />}
            color="#d32f2f"
            subtitle="Grade Levels"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <StatCard
            title="Populations"
            value={stats.total_populations}
            icon={<PopulationIcon sx={{ color: 'white' }} />}
            color="#455a64"
            subtitle="Population Records"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Latest Snapshot */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <TimeIcon sx={{ mr: 1 }} />
                Latest Data Snapshot
              </Typography>
              {stats.latest_snapshot ? (
                <Box>
                  <Typography variant="body1" color="text.secondary">
                    Last updated: {format(new Date(stats.latest_snapshot), 'PPpp')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {format(new Date(stats.latest_snapshot), 'EEEE, MMMM do, yyyy')}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body1" color="text.secondary">
                  No snapshots available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SuccessIcon sx={{ mr: 1 }} />
                System Status
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Database</Typography>
                  <Chip label="Connected" color="success" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">API</Typography>
                  <Chip label="Operational" color="success" size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Data Freshness</Typography>
                  <Chip
                    label={stats.latest_snapshot ? 'Current' : 'No Data'}
                    color={stats.latest_snapshot ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {stats.recent_activity.length > 0 ? (
                <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
                  <List dense>
                    {stats.recent_activity.map((activity, index) => (
                      <React.Fragment key={index}>
                        <ActivityItem
                          level={activity.level}
                          message={activity.message}
                          timestamp={activity.timestamp}
                          component={activity.component}
                          operation={activity.operation}
                          status={activity.status}
                        />
                        {index < stats.recent_activity.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Paper>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent activity
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
