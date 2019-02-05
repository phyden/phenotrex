#
# Created by Lukas Lüftinger on 2/5/19.
#
import logging
from typing import List, Dict, Tuple
from collections import Counter

from pica.util.logging import get_logger
from pica.data_structures.records import GenotypeRecord, PhenotypeRecord, TrainingRecord

DEFAULT_TRAIT_SIGN_MAPPING = {"YES": 1, "NO": 0}
LOGGER_TITLE = "IO"

def load_genotype_file(input_file: str) -> List[GenotypeRecord]:
    """
    Loads a genotype .TSV file and returns a list of GenotypeRecord for each entry.
    :param input_file: The path to the input genotype file.
    :return: List[GenotypeRecord] of records in the genotype file
    """
    with open(input_file) as genotype_file:
        genotype_records = []
        for line in genotype_file:
            identifier, *features = line.strip().split("\t")
            genotype_records.append(GenotypeRecord(identifier=identifier,
                                                   features=features))
    dupcount = Counter([x.identifier for x in genotype_records])
    if dupcount.most_common()[0][1] > 1:
        raise RuntimeError(f"Duplicate entries found in genotype file: {dupcount}")
    return sorted(genotype_records, key=lambda x: x.identifier)


def load_phenotype_file(input_file: str, sign_mapping: Dict[str, int]=None) -> List[PhenotypeRecord]:
    """
    Loads a phenotype .TSV file and returns a list of PhenotypeRecord for each entry.
    :param input_file: The path to the input phenotype file.
    :param sign_mapping: an optional Dict to change mappings of trait sign. Default: {"YES": 1, "NO": 0}
    :return: List[PhenotypeRecord] of records in the phenotype file
    """
    with open(input_file) as phenotype_file:
        identifiers = []
        trait_signs = []
        _, trait_name = phenotype_file.readline().strip().split("\t")
        for line in phenotype_file:
            identifier, trait_sign = line.strip().split("\t")
            identifiers.append(identifier)
            trait_signs.append(trait_sign)

    dupcount = Counter(identifiers)
    if dupcount.most_common()[0][1] > 1:
        raise RuntimeError(f"Duplicate entries found in genotype file: {dupcount}")

    if sign_mapping is None:
        sign_mapping = DEFAULT_TRAIT_SIGN_MAPPING

    trait_signs = [sign_mapping.get(x, None) for x in trait_signs]
    phenotype_records = [PhenotypeRecord(identifier=x,
                                         trait_name=trait_name,
                                         trait_sign=y) for x, y in zip(identifiers, trait_signs)]
    ret = sorted(phenotype_records, key=lambda x: x.identifier)

    return ret


def load_phenotype_and_genotype_file(genotype_file: str, phenotype_file: str, verb=False) -> Tuple[List[GenotypeRecord], List[PhenotypeRecord]]:
    """
    Convenience function to load phenotype and genotype file together.
    :param genotype_file: The path to the input genotype file.
    :param phenotype_file: The path to the input phenotype file.
    :return: Tuple[List[GenotypeRecord], List[PhenotypeRecord]] of loaded genotype and phenotype records.
    """
    logger = get_logger(LOGGER_TITLE, loglevel=logging.INFO if verb else logging.WARNING)
    gr = load_genotype_file(genotype_file)
    pr = load_phenotype_file(phenotype_file)
    logger.info("Genotype and Phenotype records successfully loaded from file.")
    return gr, pr


def collate_training_data(genotype_records, phenotype_records, verb=False) -> List[TrainingRecord]:
    """
    Returns a list of TrainingRecord from two lists of GenotypeRecord and PhenotypeRecord.
    To be used for training and CV of PICASVM.
    Checks if all genotype and phenotype records have matching identifiers,
    and if all PhenotypeRecords pertain to same trait.
    :param genotype_records: List[GenotypeRecord]
    :param phenotype_records: List[PhenotypeRecord]
    :return: List[TrainingRecord]
    """
    logger = get_logger(LOGGER_TITLE, loglevel=logging.INFO if verb else logging.WARNING)
    gr_dict  = {x.identifier: x for x in genotype_records}
    pr_dict = {x.identifier: x for x in phenotype_records}
    traits = set(x.trait_name for x in phenotype_records)
    if set(gr_dict.keys()) != set(pr_dict.keys()):
        raise RuntimeError("Different identifiers found among genotype and phenotype records. Cannot collate to TrainingRecords.")
    if len(traits) > 1:
        raise RuntimeError("More than one traits have been found in phenotype records. Cannot collate to TrainingRecords.")

    ret = [TrainingRecord(identifier=gr_dict[x].identifier,
                           trait_name=pr_dict[x].trait_name,
                           trait_sign=pr_dict[x].trait_sign,
                           features=gr_dict[x].features) for x in gr_dict.keys()]
    logger.info(f"Collated genotype and phenotype records into {len(ret)} TrainingRecord.")
    return ret
