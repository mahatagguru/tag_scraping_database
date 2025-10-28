import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Chip,
  Button,
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
  Paper,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  CardGiftcard as CardIcon,
  Grade as GradeIcon,
  Timeline as PopulationIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getCategories, getCardsBySet } from '../services/api';
import { Category, Card } from '../types';

const CardItem: React.FC<{
  card: Card;
  onViewDetails: (card: Card) => void;
}> = ({ card, onViewDetails }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
        <CardIcon sx={{ mr: 1, color: 'primary.main', mt: 0.5 }} />
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
            {card.player || 'Unknown Player'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {card.category_name} • {card.year} • {card.set_name}
          </Typography>
        </Box>
        <Button
          size="small"
          startIcon={<ViewIcon />}
          onClick={() => onViewDetails(card)}
        >
          View
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        {card.card_number && (
          <Chip
            label={`#${card.card_number}`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
        {card.cert_number && (
          <Chip
            label={`Cert: ${card.cert_number}`}
            size="small"
            color="secondary"
            variant="outlined"
          />
        )}
        {card.subset_name && (
          <Chip
            label={card.subset_name}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
        {card.variation && (
          <Chip
            label={card.variation}
            size="small"
            color="warning"
            variant="outlined"
          />
        )}
      </Box>

      <Typography variant="caption" color="text.secondary">
        Updated: {new Date(card.updated_at).toLocaleDateString()}
      </Typography>
    </CardContent>
  </Card>
);

const Cards: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | ''>('');
  const [selectedSet, setSelectedSet] = useState<number | ''>('');
  const [page, setPage] = useState(1);
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const itemsPerPage = 12;

  const { data: categories, isLoading: categoriesLoading } = useQuery(
    'categories',
    () => getCategories(true, 100, 0)
  );

  // Get all cards by fetching from all sets
  const { data: allCards, isLoading: cardsLoading, error } = useQuery(
    'all-cards',
    async () => {
      if (!categories) return [];

      const allCards: Card[] = [];

      // This is a simplified approach - in a real app, you'd want a dedicated endpoint
      for (const category of categories) {
        try {
          // This would need to be implemented in the backend
          // For now, we'll show a message that cards need to be loaded
          break;
        } catch (error) {
          console.error(`Error loading cards for category ${category.id}:`, error);
        }
      }

      return allCards;
    },
    {
      enabled: !!categories,
    }
  );

  const filteredCards = useMemo(() => {
    if (!allCards) return [];

    return allCards.filter((card) => {
      const matchesSearch =
        card.player?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.card_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.cert_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        card.set_name.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesCategory = !selectedCategory || card.category_id === selectedCategory;
      const matchesSet = !selectedSet || card.set_id === selectedSet;

      return matchesSearch && matchesCategory && matchesSet;
    });
  }, [allCards, searchTerm, selectedCategory, selectedSet]);

  const paginatedCards = useMemo(() => {
    const startIndex = (page - 1) * itemsPerPage;
    return filteredCards.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredCards, page, itemsPerPage]);

  const totalPages = Math.ceil(filteredCards.length / itemsPerPage);

  const handleCategoryChange = (event: SelectChangeEvent<number | ''>) => {
    setSelectedCategory(event.target.value as number | '');
    setSelectedSet('');
    setPage(1);
  };

  const handleSetChange = (event: SelectChangeEvent<number | ''>) => {
    setSelectedSet(event.target.value as number | '');
    setPage(1);
  };

  const handleViewDetails = (card: Card) => {
    setSelectedCard(card);
  };

  if (categoriesLoading || cardsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load cards. Please check your connection and try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3 }}>
        Cards Database
      </Typography>

      {/* Search and Filters */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            placeholder="Search cards by player, number, certificate..."
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
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
        </Box>

        {showFilters && (
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <FormControl sx={{ minWidth: 200 }}>
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

            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Set</InputLabel>
              <Select
                value={selectedSet}
                onChange={handleSetChange}
                label="Set"
                disabled={!selectedCategory}
              >
                <MenuItem value="">
                  <em>All Sets</em>
                </MenuItem>
                {/* Sets would be loaded based on selected category */}
              </Select>
            </FormControl>
          </Box>
        )}
      </Box>

      {/* Results Summary */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          {filteredCards.length} cards found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Page {page} of {totalPages}
        </Typography>
      </Box>

      {/* Cards Grid */}
      {paginatedCards.length > 0 ? (
        <>
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {paginatedCards.map((card) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={card.id}>
                <CardItem
                  card={card}
                  onViewDetails={handleViewDetails}
                />
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </>
      ) : (
        <Alert severity="info">
          {allCards && allCards.length === 0
            ? 'No cards found in the database. Run the scraping pipeline to populate data.'
            : 'No cards match your search criteria. Try adjusting your filters.'}
        </Alert>
      )}

      {/* Card Details Dialog */}
      <Dialog
        open={!!selectedCard}
        onClose={() => setSelectedCard(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Card Details</DialogTitle>
        <DialogContent>
          {selectedCard && (
            <Box>
              <Typography variant="h5" gutterBottom>
                {selectedCard.player || 'Unknown Player'}
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Category</strong></TableCell>
                        <TableCell>{selectedCard.category_name}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Year</strong></TableCell>
                        <TableCell>{selectedCard.year}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Set</strong></TableCell>
                        <TableCell>{selectedCard.set_name}</TableCell>
                      </TableRow>
                      {selectedCard.card_number && (
                        <TableRow>
                          <TableCell><strong>Card Number</strong></TableCell>
                          <TableCell>{selectedCard.card_number}</TableCell>
                        </TableRow>
                      )}
                      {selectedCard.cert_number && (
                        <TableRow>
                          <TableCell><strong>Certificate Number</strong></TableCell>
                          <TableCell>{selectedCard.cert_number}</TableCell>
                        </TableRow>
                      )}
                      {selectedCard.subset_name && (
                        <TableRow>
                          <TableCell><strong>Subset</strong></TableCell>
                          <TableCell>{selectedCard.subset_name}</TableCell>
                        </TableRow>
                      )}
                      {selectedCard.variation && (
                        <TableRow>
                          <TableCell><strong>Variation</strong></TableCell>
                          <TableCell>{selectedCard.variation}</TableCell>
                        </TableRow>
                      )}
                      <TableRow>
                        <TableCell><strong>Last Updated</strong></TableCell>
                        <TableCell>{new Date(selectedCard.updated_at).toLocaleString()}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>

              {selectedCard.detail_url && (
                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    href={selectedCard.detail_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View Original Details
                  </Button>
                </Box>
              )}

              {selectedCard.image_url && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Card Image
                  </Typography>
                  <img
                    src={selectedCard.image_url}
                    alt={`${selectedCard.player} card`}
                    style={{ maxWidth: '100%', height: 'auto', borderRadius: 8 }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedCard(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Cards;
