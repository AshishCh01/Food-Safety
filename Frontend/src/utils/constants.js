export const ROLES = {
  CITIZEN: 'citizen',
  INSPECTOR: 'inspector',
  DISTRICT_OFFICER: 'district_officer',
  ADMIN: 'admin',
  FOOD_ANALYST: 'food_analyst',
};

export const DASHBOARD_PATH_BY_ROLE = {
  [ROLES.CITIZEN]: '/citizen',
  [ROLES.INSPECTOR]: '/inspector',
  [ROLES.DISTRICT_OFFICER]: '/officer',
  [ROLES.ADMIN]: '/admin',
  [ROLES.FOOD_ANALYST]: '/food-analyst',
};
