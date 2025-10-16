import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Category as CategoryIcon,
  CalendarToday as YearIcon,
  CardGiftcard as SetIcon,
  CardGiftcard as CardIcon,
  Timeline as PopulationIcon,
} from '@mui/icons-material';
import { useQuery } from 'react-query';
import { getCategories, getYearsByCategory, getSetsByYear, getCardsBySet } from '../services/api';
import { Category, Year, Set, Card } from '../types';

const CategoryCard: React.FC<{
  category: Category;
  onExpand: () => void;
  isExpanded: boolean;
}> = ({ category, onExpand, isExpanded }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <CategoryIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {category.name}
        </Typography>
        <IconButton onClick={onExpand} size="small">
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>
      
      {category.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {category.description}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        {category.num_sets && (
          <Chip
            icon={<SetIcon />}
            label={`${category.num_sets} Sets`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
        {category.total_items && (
          <Chip
            icon={<CardIcon />}
            label={`${category.total_items.toLocaleString()} Items`}
            size="small"
            color="secondary"
            variant="outlined"
          />
        )}
        {category.total_graded && (
          <Chip
            icon={<PopulationIcon />}
            label={`${category.total_graded.toLocaleString()} Graded`}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
      </Box>

      <Typography variant="caption" color="text.secondary">
        Updated: {new Date(category.updated_at).toLocaleDateString()}
      </Typography>
    </CardContent>
  </Card>
);

const YearCard: React.FC<{
  year: Year;
  onExpand: () => void;
  isExpanded: boolean;
}> = ({ year, onExpand, isExpanded }) => (
  <Card sx={{ ml: 2, mb: 1 }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <YearIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {year.year}
        </Typography>
        <IconButton onClick={onExpand} size="small">
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        {year.num_sets && (
          <Chip
            icon={<SetIcon />}
            label={`${year.num_sets} Sets`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
        {year.total_items && (
          <Chip
            icon={<CardIcon />}
            label={`${year.total_items.toLocaleString()} Items`}
            size="small"
            color="secondary"
            variant="outlined"
          />
        )}
        {year.total_graded && (
          <Chip
            icon={<PopulationIcon />}
            label={`${year.total_graded.toLocaleString()} Graded`}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
      </Box>
    </CardContent>
  </Card>
);

const SetCard: React.FC<{
  set: Set;
  onExpand: () => void;
  isExpanded: boolean;
}> = ({ set, onExpand, isExpanded }) => (
  <Card sx={{ ml: 4, mb: 1 }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <SetIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {set.set_name}
        </Typography>
        <IconButton onClick={onExpand} size="small">
          {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </IconButton>
      </Box>

      {set.set_description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {set.set_description}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        {set.num_cards && (
          <Chip
            icon={<CardIcon />}
            label={`${set.num_cards} Cards`}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
        {set.total_items && (
          <Chip
            icon={<CardIcon />}
            label={`${set.total_items.toLocaleString()} Items`}
            size="small"
            color="secondary"
            variant="outlined"
          />
        )}
        {set.total_graded && (
          <Chip
            icon={<PopulationIcon />}
            label={`${set.total_graded.toLocaleString()} Graded`}
            size="small"
            color="success"
            variant="outlined"
          />
        )}
      </Box>
    </CardContent>
  </Card>
);

const CardList: React.FC<{
  cards: Card[];
  onCardClick: (card: Card) => void;
}> = ({ cards, onCardClick }) => (
  <Box sx={{ ml: 6 }}>
    <Typography variant="subtitle2" gutterBottom>
      Cards ({cards.length})
    </Typography>
    <List dense>
      {cards.map((card) => (
        <ListItem
          key={card.id}
          button
          onClick={() => onCardClick(card)}
          sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}
        >
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {card.player || 'Unknown Player'}
                </Typography>
                {card.card_number && (
                  <Chip label={`#${card.card_number}`} size="small" variant="outlined" />
                )}
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="body2" color="text.secondary">
                  {card.set_name} • {card.year}
                </Typography>
                {card.subset_name && (
                  <Typography variant="caption" color="text.secondary">
                    {card.subset_name}
                  </Typography>
                )}
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  </Box>
);

const Categories: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<number>>(new Set());
  const [expandedYears, setExpandedYears] = useState<Set<number>>(new Set());
  const [expandedSets, setExpandedSets] = useState<Set<number>>(new Set());
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);

  const { data: categories, isLoading, error } = useQuery(
    'categories',
    () => getCategories(true, 100, 0),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  );

  const handleCategoryExpand = (categoryId: number) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  const handleYearExpand = (yearId: number) => {
    const newExpanded = new Set(expandedYears);
    if (newExpanded.has(yearId)) {
      newExpanded.delete(yearId);
    } else {
      newExpanded.add(yearId);
    }
    setExpandedYears(newExpanded);
  };

  const handleSetExpand = (setId: number) => {
    const newExpanded = new Set(expandedSets);
    if (newExpanded.has(setId)) {
      newExpanded.delete(setId);
    } else {
      newExpanded.add(setId);
    }
    setExpandedSets(newExpanded);
  };

  const handleCardClick = (card: Card) => {
    setSelectedCard(card);
  };

  const filteredCategories = categories?.filter((category) =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (category.description && category.description.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

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
        Failed to load categories. Please check your connection and try again.
      </Alert>
    );
  }

  if (!categories || categories.length === 0) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        No categories available. The database appears to be empty. Run the scraping pipeline to populate data.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 3 }}>
        Categories & Data Hierarchy
      </Typography>

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search categories, descriptions..."
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
      </Box>

      <Grid container spacing={3}>
        {filteredCategories.map((category) => (
          <Grid item xs={12} md={6} lg={4} key={category.id}>
            <CategoryCard
              category={category}
              onExpand={() => handleCategoryExpand(category.id)}
              isExpanded={expandedCategories.has(category.id)}
            />
            
            {expandedCategories.has(category.id) && (
              <CategoryDetails
                categoryId={category.id}
                expandedYears={expandedYears}
                expandedSets={expandedSets}
                onYearExpand={handleYearExpand}
                onSetExpand={handleSetExpand}
                onCardClick={handleCardClick}
              />
            )}
          </Grid>
        ))}
      </Grid>

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
              <Typography variant="h6" gutterBottom>
                {selectedCard.player || 'Unknown Player'}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {selectedCard.category_name} • {selectedCard.year} • {selectedCard.set_name}
              </Typography>
              {selectedCard.card_number && (
                <Typography variant="body2" gutterBottom>
                  Card Number: {selectedCard.card_number}
                </Typography>
              )}
              {selectedCard.cert_number && (
                <Typography variant="body2" gutterBottom>
                  Certificate: {selectedCard.cert_number}
                </Typography>
              )}
              {selectedCard.subset_name && (
                <Typography variant="body2" gutterBottom>
                  Subset: {selectedCard.subset_name}
                </Typography>
              )}
              {selectedCard.variation && (
                <Typography variant="body2" gutterBottom>
                  Variation: {selectedCard.variation}
                </Typography>
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

const CategoryDetails: React.FC<{
  categoryId: number;
  expandedYears: Set<number>;
  expandedSets: Set<number>;
  onYearExpand: (yearId: number) => void;
  onSetExpand: (setId: number) => void;
  onCardClick: (card: Card) => void;
}> = ({ categoryId, expandedYears, expandedSets, onYearExpand, onSetExpand, onCardClick }) => {
  const { data: years } = useQuery(
    ['years', categoryId],
    () => getYearsByCategory(categoryId, true, 50, 0),
    {
      enabled: true,
    }
  );

  return (
    <Box sx={{ mt: 2 }}>
      {years?.map((year) => (
        <React.Fragment key={year.id}>
          <YearCard
            year={year}
            onExpand={() => onYearExpand(year.id)}
            isExpanded={expandedYears.has(year.id)}
          />
          
          {expandedYears.has(year.id) && (
            <YearDetails
              yearId={year.id}
              expandedSets={expandedSets}
              onSetExpand={onSetExpand}
              onCardClick={onCardClick}
            />
          )}
        </React.Fragment>
      ))}
    </Box>
  );
};

const YearDetails: React.FC<{
  yearId: number;
  expandedSets: Set<number>;
  onSetExpand: (setId: number) => void;
  onCardClick: (card: Card) => void;
}> = ({ yearId, expandedSets, onSetExpand, onCardClick }) => {
  const { data: sets } = useQuery(
    ['sets', yearId],
    () => getSetsByYear(yearId, true, 50, 0),
    {
      enabled: true,
    }
  );

  return (
    <Box>
      {sets?.map((set) => (
        <React.Fragment key={set.id}>
          <SetCard
            set={set}
            onExpand={() => onSetExpand(set.id)}
            isExpanded={expandedSets.has(set.id)}
          />
          
          {expandedSets.has(set.id) && (
            <SetDetails setId={set.id} onCardClick={onCardClick} />
          )}
        </React.Fragment>
      ))}
    </Box>
  );
};

const SetDetails: React.FC<{
  setId: number;
  onCardClick: (card: Card) => void;
}> = ({ setId, onCardClick }) => {
  const { data: cards } = useQuery(
    ['cards', setId],
    () => getCardsBySet(setId, true, 20, 0),
    {
      enabled: true,
    }
  );

  if (!cards) return null;

  return <CardList cards={cards} onCardClick={onCardClick} />;
};

export default Categories;
