## Description

**Paper** 10.1007/978-3-030-58942-4
**Data** https://bitbucket.org/satt/examtimetablinguniuddata/src/master/

### Definition

Our problem consists of scheduling an examination session at the end of a semester for a university campus. The problem is based on the following entities:

- Courses, Exams, & Events: For each course, we have to schedule one or more exams within the session. Each exam might be a single event (either written or oral) or composed by two events, identified as the written part (first) and the oral part (second), to be handed out in this strict order.
- Rooms & Roomsets: Some events require one or more rooms, others do not, as they take place in teacher’s office or in external rooms. Rooms are classified as small, medium, or large, and for each written event we set the number and the type of rooms requested (mixed requests are not considered). Due to logistic issues, not all combinations of homogeneous rooms can be assigned to a single event. The available ones, called roomsets, are explicitly listed in the input data. Oral events might require at most one room (of any size).
- Days, Timeslots, & Periods: The session is divided in days and each day in divided in timeslots, with the same number of timeslots for each day. Each pair day/timeslot represents a period of the session.
- Curricula: A curriculum is a set of courses that have students in common, which might enroll in the corresponding exams. The set of courses of a curriculum is split into primary courses, that are the ones taught in the current semester, and the secondary ones, that have been taught in the previous semester, but such that some students might still have to undertake them. The level of conflict between primary and secondary exams of a curriculum varies, as detailed below.

### Hard Constraints
**H1. RoomRequest** 
for each written event, type and number of the rooms assigned must be correct; for oral exams, a single room, of any type, must be assigned, if requested.

**H2. RoomOccupation**
in one period, a room can be used by at most one event.

**H3. HardConflicts**
Two events in hard conflict cannot be scheduled in the same period. Two events are in hard conflict in the following cases:
- They are part of courses that are both primary courses of one curriculum.
- They have the same teacher.
- There is an explicit constraint stating that the overlap of the two events is forbidden.

**H4. Precedences**
When two events have a precedence constraint, the first must be scheduled strictly before the second. Two events have a precedence constraint in the following cases:
- They are part of two exams of the same course.
- They are part of the same exam (written and oral).

**H5. Unavailabilities**
An event might be explicitly stated as unavailable in a specific period, so that it cannot be assigned to that period. 

### Soft Constraints

**S1. SoftConflicts**
Two events in soft conflict should not be scheduled in the same period. Two events are in soft conflict in the following cases:
- They belong to courses that are in the same curriculum, either as primary
and secondary or both as secondary.
- There is an explicit constraint stating that their overlap is undesirable.

**S2. Preferences**
Like Unavailabilities, preferences between events and periods and between periods and rooms stating the undesirability of an assignment can be expressed explicitly. For periods, it is also possible to state a positive preference for a specific event, so that in presence of preferred periods for an event, all indifferent ones are assumed undesired (and explicitly undesired one are given a larger penalty).

**S3. Distances**
Among events there might be requested separations in term of periods. Distances can be either directed, imposing that one event must precede the other, or undirected so that any order is acceptable. The situations that require a distance are the following:
- Same exam (directed): different parts of the same exam have a minimum and a maximum distance, stated specifically for each course (e.g., events 0 and 1 in the example).
- Same course (directed): different exams of the same course must be separated. The separation constraint is applied between the first (or single) part of each of the two exams (e.g., events 0 and 2 in the example).
- Same curriculum (undirected): if two courses belong to the same curriculum, there should be a separation between the exams (as above, for two-part exams, we consider the first one). The amount of separation and the weight for its violation depend on the type of the two (primary or secondary) memberships.
- Additional requests can be added explicitly