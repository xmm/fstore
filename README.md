# FSTORE project

## Requirements
### Vision
#### Problem

Saving and recovering data takes too long time in internal projects of a company.

#### Task

Provide a reliable service for keeping, returning and transforming images (and another files). The service must have features for easy administering by storages (adding, removing, archiving)

#### Base features ###

 * Save files in the storage
 * Returns files in requested formats defined in a configuration file
 * Ability to use several disk storages
 * Automatic distribute of files in storages
 * Prevent to overflow storages
 * Ability to move a file between storages without changing an URL of the file

#### Users of the system ###

 * _Services_: saves files
 * _Users_: requests files in required format
 * _Admin_: administer storages (adding, removing, archiving and recovering storages). TODO

### Additional requirements ###

#### Security
 * _Service_ must authenticate yourself for saving files

#### Performance
 * The main priority is a response for _Users_ request. File transforming should not to affect to other requests.
 * Ability to horizontal scaling (for performance and reliability)

#### Duplicated files
 * Advisable don't duplicate files with identical content. (Name of files don't have a value)

### Terms
 * _Services_ - the internal services of a company
 * _Users_ - users of the internal services
 * _Storage_ - file systems used for keeping a files of _Services_

### Use cases
 * Save a file
 * Returns file in a format
 * File transformation
 * Adding a storage
 * Moving files from a degrading storage TODO
 * Recovering files from an archive TODO

