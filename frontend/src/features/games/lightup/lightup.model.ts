export enum LightupCellStates {
  Wall0 = 0,
  Wall1 = 1,
  Wall2 = 2,
  Wall3 = 3,
  Wall4 = 4,
  WallBlank = 5,
  Empty = 6,
  Bulb = 7,
  Cross = 8,
  NUM_STATES,
}

export const LightWallStates = [
  LightupCellStates.Wall0,
  LightupCellStates.Wall1,
  LightupCellStates.Wall2,
  LightupCellStates.Wall3,
  LightupCellStates.Wall4,
  LightupCellStates.WallBlank,
];
