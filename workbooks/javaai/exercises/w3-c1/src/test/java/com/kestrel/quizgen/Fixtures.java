package com.kestrel.quizgen;

import java.util.List;

public final class Fixtures {
    private Fixtures() { }

    public static final Model.Lesson LESSON = new Model.Lesson("bio-101-l3", "Cell membranes", List.of(
            new Model.Section("s1", "Structure", "The membrane is a phospholipid bilayer with embedded proteins."),
            new Model.Section("s2", "Transport", "Small non-polar molecules diffuse; ions need channel proteins."),
            new Model.Section("s3", "Osmosis", "Water moves toward the higher solute concentration.")));

    public static String item(String stem, String a, String b, String c, String d, int answer, String explanation, String section) {
        return "{\"stem\":\"" + stem + "\",\"options\":[\"" + a + "\",\"" + b + "\",\"" + c + "\",\"" + d + "\"],"
                + "\"answerIndex\":" + answer + ",\"explanation\":\"" + explanation + "\",\"sectionId\":\"" + section + "\"}";
    }

    public static final String ITEM1 = item("What is the basic structure of the cell membrane?",
            "A phospholipid bilayer", "A cellulose wall", "A single protein sheet", "A starch lattice", 0,
            "Section s1 describes a bilayer of phospholipids.", "s1");
    public static final String ITEM2 = item("How do ions usually cross the membrane?",
            "Through channel proteins", "By simple diffusion", "They cannot cross", "By osmosis", 0,
            "Section s2: ions need channel proteins.", "s2");
    public static final String ITEM3 = item("In osmosis, where does water move?",
            "Toward lower solute concentration", "Toward higher solute concentration", "It does not move", "Only into the nucleus", 1,
            "Section s3: water moves toward the higher solute concentration.", "s3");

    public static String envelope(String... items) { return "{\"items\":[" + String.join(",", items) + "]}"; }

    public static final String VALID3 = envelope(ITEM1, ITEM2, ITEM3);
}
