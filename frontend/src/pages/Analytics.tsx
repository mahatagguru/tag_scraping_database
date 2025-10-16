import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { useQuery } from 'react-query';
import { getCategories, getPopulationTrends, getGrades } from '../services/api';
import { Category, Grade } from '../types';

const COLORS = [
  '#1976d2',
  '#388e3c',
  '#f57c00',
  '#d32f2f',
  '#7b1fa2',
  '#455a64',
  '#e91e63',
  '#00bcd4',
  '#ff9800',
  '#4caf50',
];

const Analytics: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<number | ''>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('');
  const [timeRange, setTimeRange] = useState<number>(30);

  const { data: categories, isLoading: categoriesLoading } = useQuery(
    'categories',
    () => getCategories(true, 100, 0)
  );

  const { data: grades, isLoading: gradesLoading } = useQuery(
    'grades',
    () => getGrades(true, 100)
  );

  const { data: populationTrends, isLoading: trendsLoading } = useQuery(
    ['population-trends', selectedCategory, selectedGrade, timeRange],
    () => getPopulationTrends(
      selectedCategory ? `category_${selectedCategory}` : undefined,
      selectedGrade || undefined,
      timeRange
    ),
    {
      enabled: true,
    }
  );

  const handleCategoryChange = (event: SelectChangeEvent<number | ''>) => {
    setSelectedCategory(event.target.value as number | '');
  };

  const handleGradeChange = (event: SelectChangeEvent<string>) => {
    setSelectedGrade(event.target.value);
  };

  const handleTimeRangeChange = (event: SelectChangeEvent<number>) => {
    setTimeRange(event.target.value as number);
  };

  // Mock data for demonstration (replace with real data when available)
  const mockCategoryData = [
    { name: 'Baseball', cards: 1250, sets: 45, graded: 3200 },
    { name: 'Basketball', cards: 890, sets: 32, graded: 2100 },
    { name: 'Football', cards: 1100, sets: 38, graded: 2800 },
    { name: 'Hockey', cards: 750, sets: 28, graded: 1800 },
  ];

  const mockGradeDistribution = [
    { name: '10', value: 45, count: 450 },
    { name: '9.5', value: 35, count: 350 },
    { name: '9', value: 25, count: 250 },
    { name: '8.5', value: 15, count: 150 },
    { name: '8', value: 10, count: 100 },
    { name: '7.5', value: 8, count: 80 },
    { name: '7', value: 5, count: 50 },
  ];

  const mockTrendData = [
    { date: '2024-01-01', total: 1000, graded: 800 },
    { date: '2024-01-02', total: 1050, graded: 850 },
    { date: '2024-01-03', total: 1100, graded: 900 },
    { date: '2024-01-04', total: 1150, graded: 950 },
    { date: '2024-01-05', total: 1200, graded: 1000 },
    { date: '2024-01-06', total: 1250, graded: 1050 },
    { date: '2024-01-07', total: 1300, graded: 1100 },
  ];

  if (categoriesLoading || gradesLoading || trendsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3 }}>
        Analytics & Insights
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={selectedCategory}
                  onChange={handleCategoryChange}
                  label="Category"
                >
                  <MenuItem value="">
                    <em>All Categories</em>
                  </MenuItem>
                  {categories?.map((category) => (
                    <MenuItem key={category.id} value={category.id}>
                      {category.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Grade</InputLabel>
                <Select
                  value={selectedGrade}
                  onChange={handleGradeChange}
                  label="Grade"
                >
                  <MenuItem value="">
                    <em>All Grades</em>
                  </MenuItem>
                  {grades?.map((grade) => (
                    <MenuItem key={grade.id} value={grade.grade_label}>
                      {grade.grade_label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Time Range</InputLabel>
                <Select
                  value={timeRange}
                  onChange={handleTimeRangeChange}
                  label="Time Range"
                >
                  <MenuItem value={7}>Last 7 days</MenuItem>
                  <MenuItem value={30}>Last 30 days</MenuItem>
                  <MenuItem value={90}>Last 90 days</MenuItem>
                  <MenuItem value={365}>Last year</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Category Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cards by Category
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mockCategoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="cards" fill="#1976d2" name="Cards" />
                  <Bar dataKey="sets" fill="#388e3c" name="Sets" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Grade Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Grade Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={mockGradeDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {mockGradeDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Population Trends */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Population Trends Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={mockTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="total"
                    stroke="#1976d2"
                    strokeWidth={2}
                    name="Total Cards"
                  />
                  <Line
                    type="monotone"
                    dataKey="graded"
                    stroke="#388e3c"
                    strokeWidth={2}
                    name="Graded Cards"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Grade Statistics Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Grade Statistics
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Grade</strong></TableCell>
                      <TableCell align="right"><strong>Count</strong></TableCell>
                      <TableCell align="right"><strong>Percentage</strong></TableCell>
                      <TableCell align="right"><strong>Value</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockGradeDistribution.map((grade, index) => (
                      <TableRow key={grade.name}>
                        <TableCell>
                          <Chip
                            label={grade.name}
                            size="small"
                            sx={{ backgroundColor: COLORS[index % COLORS.length], color: 'white' }}
                          />
                        </TableCell>
                        <TableCell align="right">{grade.count.toLocaleString()}</TableCell>
                        <TableCell align="right">
                          {((grade.value / 100) * 100).toFixed(1)}%
                        </TableCell>
                        <TableCell align="right">
                          {grade.value > 0 ? `$${(grade.value * 10).toFixed(2)}` : 'N/A'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Population Trends Data */}
        {populationTrends && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Population Trends Data
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  This data is based on the current database state. Historical trends require population_reports table data.
                </Alert>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {Object.entries(populationTrends.trends).map(([grade, count]) => (
                    <Chip
                      key={grade}
                      label={`${grade}: ${count.toLocaleString()}`}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Total Cards: {populationTrends.total_cards.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Date Range: {new Date(populationTrends.date_range.start).toLocaleDateString()} - {new Date(populationTrends.date_range.end).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Analytics;
