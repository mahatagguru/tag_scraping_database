import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Search as SearchIcon,
  Category as CategoryIcon,
  CalendarToday as YearIcon,
  CardGiftcard as SetIcon,
  CardGiftcard as CardIcon,
  Grade as GradeIcon,
  Visibility as ViewIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { search } from '../services/api';
import { SearchResult } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`search-tabpanel-${index}`}
    aria-labelledby={`search-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const SearchResultItem: React.FC<{
  result: SearchResult;
  onViewDetails: (result: SearchResult) => void;
}> = ({ result, onViewDetails }) => {
  const getIcon = () => {
    switch (result.type) {
      case 'category':
        return <CategoryIcon color="primary" />;
      case 'year':
        return <YearIcon color="primary" />;
      case 'set':
        return <SetIcon color="primary" />;
      case 'card':
        return <CardIcon color="primary" />;
      default:
        return <SearchIcon color="primary" />;
    }
  };

  const getTypeColor = () => {
    switch (result.type) {
      case 'category':
        return 'primary';
      case 'year':
        return 'secondary';
      case 'set':
        return 'success';
      case 'card':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <ListItem
      button
      onClick={() => onViewDetails(result)}
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        mb: 1,
        '&:hover': {
          backgroundColor: 'action.hover',
        },
      }}
    >
      <ListItemIcon>{getIcon()}</ListItemIcon>
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
              {result.name}
            </Typography>
            <Chip
              label={result.type.toUpperCase()}
              size="small"
              color={getTypeColor() as any}
              variant="outlined"
            />
          </Box>
        }
        secondary={
          <Box>
            <Typography variant="body2" color="text.secondary">
              {result.description}
            </Typography>
            {result.category && (
              <Typography variant="caption" color="text.secondary">
                Category: {result.category}
                {result.year && ` • Year: ${result.year}`}
                {result.set_name && ` • Set: ${result.set_name}`}
              </Typography>
            )}
          </Box>
        }
      />
      <ListItemSecondaryAction>
        <Button
          size="small"
          startIcon={<ViewIcon />}
          onClick={() => onViewDetails(result)}
        >
          View
        </Button>
      </ListItemSecondaryAction>
    </ListItem>
  );
};

const Search: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const { data: searchData, isLoading, error } = useQuery(
    ['search', searchTerm],
    () => search(searchTerm, 100),
    {
      enabled: searchTerm.length >= 2,
      onSuccess: (data) => {
        setSearchResults(data);
        setIsSearching(false);
      },
      onError: () => {
        setIsSearching(false);
      },
    }
  );

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault();
    if (searchTerm.length >= 2) {
      setIsSearching(true);
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setSearchResults([]);
    setTabValue(0);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewDetails = (result: SearchResult) => {
    setSelectedResult(result);
  };

  const filteredResults = useMemo(() => {
    if (!searchResults) return [];

    const typeMap = {
      0: 'all',
      1: 'card',
      2: 'set',
      3: 'year',
      4: 'category',
    };

    const selectedType = typeMap[tabValue as keyof typeof typeMap];

    if (selectedType === 'all') {
      return searchResults;
    }

    return searchResults.filter(result => result.type === selectedType);
  }, [searchResults, tabValue]);

  const getResultCounts = () => {
    if (!searchResults) return { all: 0, card: 0, set: 0, year: 0, category: 0 };

    return searchResults.reduce(
      (counts, result) => {
        counts.all++;
        counts[result.type]++;
        return counts;
      },
      { all: 0, card: 0, set: 0, year: 0, category: 0 }
    );
  };

  const counts = getResultCounts();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3 }}>
        Search Database
      </Typography>

      {/* Search Form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={handleSearch}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                fullWidth
                placeholder="Search cards, sets, years, categories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
              <Button
                type="submit"
                variant="contained"
                disabled={searchTerm.length < 2 || isSearching}
              >
                {isSearching ? <CircularProgress size={20} /> : 'Search'}
              </Button>
              {searchTerm && (
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={handleClearSearch}
                >
                  Clear
                </Button>
              )}
            </Box>
          </form>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchTerm && (
        <Card>
          <CardContent>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label={`All (${counts.all})`} />
                <Tab label={`Cards (${counts.card})`} />
                <Tab label={`Sets (${counts.set})`} />
                <Tab label={`Years (${counts.year})`} />
                <Tab label={`Categories (${counts.category})`} />
              </Tabs>
            </Box>

            {isLoading || isSearching ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : error ? (
              <Alert severity="error">
                Failed to search. Please check your connection and try again.
              </Alert>
            ) : filteredResults.length === 0 ? (
              <Alert severity="info">
                {searchTerm.length < 2
                  ? 'Enter at least 2 characters to search'
                  : 'No results found. Try different search terms.'}
              </Alert>
            ) : (
              <Paper variant="outlined" sx={{ maxHeight: 600, overflow: 'auto' }}>
                <List>
                  {filteredResults.map((result, index) => (
                    <React.Fragment key={`${result.type}-${result.id}`}>
                      <SearchResultItem
                        result={result}
                        onViewDetails={handleViewDetails}
                      />
                      {index < filteredResults.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </Paper>
            )}
          </CardContent>
        </Card>
      )}

      {/* Result Details Dialog */}
      <Dialog
        open={!!selectedResult}
        onClose={() => setSelectedResult(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Search Result Details</DialogTitle>
        <DialogContent>
          {selectedResult && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="h5">
                  {selectedResult.name}
                </Typography>
                <Chip
                  label={selectedResult.type.toUpperCase()}
                  color="primary"
                  variant="outlined"
                />
              </Box>

              {selectedResult.description && (
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  {selectedResult.description}
                </Typography>
              )}

              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Property</strong></TableCell>
                      <TableCell><strong>Value</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Type</TableCell>
                      <TableCell>{selectedResult.type}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>{selectedResult.id}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>{selectedResult.name}</TableCell>
                    </TableRow>
                    {selectedResult.description && (
                      <TableRow>
                        <TableCell>Description</TableCell>
                        <TableCell>{selectedResult.description}</TableCell>
                      </TableRow>
                    )}
                    {selectedResult.category && (
                      <TableRow>
                        <TableCell>Category</TableCell>
                        <TableCell>{selectedResult.category}</TableCell>
                      </TableRow>
                    )}
                    {selectedResult.year && (
                      <TableRow>
                        <TableCell>Year</TableCell>
                        <TableCell>{selectedResult.year}</TableCell>
                      </TableRow>
                    )}
                    {selectedResult.set_name && (
                      <TableRow>
                        <TableCell>Set</TableCell>
                        <TableCell>{selectedResult.set_name}</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedResult(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Search;
