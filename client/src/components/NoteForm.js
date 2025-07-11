import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";
import { useFormik } from "formik";
import * as yup from "yup";
import {
  Button,
  Box,
  FormLabel,
  FormControl,
  FormHelperText,
  Textarea,
  Select,
  Option,
  Slider,
} from "@mui/joy";

const formSchema = yup.object().shape({
  rating: yup
    .number()
    .required("Must provide a rating")
    .min(1, "Rating must be at least 1")
    .max(5, "Rating must be at most 5"),
  comment: yup
    .string()
    .required("Must enter a comment")
    .max(500, "Comment should be less than 500 characters"),
  coffee_id: yup.number().required("Must select a coffee"),
});

function NoteForm({ onNoteAdded, onCancel, existingNote = null }) {
  const isEditing = Boolean(existingNote);
  const { cafes, allCoffees } = useUser();
  const navigate = useNavigate();
  const [selectedCafeId, setSelectedCafeId] = useState(
    existingNote?.coffee?.cafe_id || ""
  );

  const formik = useFormik({
    initialValues: {
      rating: existingNote?.rating || 3,
      comment: existingNote?.comment || "",
      coffee_id: existingNote?.coffee_id || "",
    },
    validationSchema: formSchema,
    onSubmit: (values) => {
      const url = isEditing ? `/notes/${existingNote.id}` : "/notes";
      const method = isEditing ? "PATCH" : "POST";

      fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify(values),
      })
        .then((response) => {
          if (!response.ok) throw new Error("Failed to save note");
          return response.json();
        })
        .then((noteData) => {
          onNoteAdded(noteData);
          if (!isEditing) formik.resetForm();
          if (onCancel) onCancel();
        })
        .catch((error) => {
          console.error("Error saving note:", error);
        });
    },
  });

  const filteredCoffees = allCoffees.filter(
    (allCoffees) => allCoffees.cafe?.id === selectedCafeId
  );

  const getRatingLabel = (value) => {
    const labels = {
      1: "Poor",
      2: "Fair",
      3: "Good",
      4: "Very Good",
      5: "Excellent",
    };
    return labels[value] || "";
  };

  return (
    <Box
      sx={{
        p: 3,
        bgcolor: "background.surface",
        borderRadius: "md",
        border: "1px solid",
        borderColor: "divider",
      }}
    >
      <Box component="form" onSubmit={formik.handleSubmit}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {/* Cafe dropdown */}
          <FormControl>
            <FormLabel>Cafe</FormLabel>
            <Select
              value={selectedCafeId}
              onChange={(e, val) => {
                setSelectedCafeId(val);
                formik.setFieldValue("coffee_id", ""); // clear coffee selection
              }}
              placeholder="Select a cafe"
            >
              {cafes.map((cafe) => (
                <Option key={cafe.id} value={cafe.id}>
                  {cafe.name} - {cafe.location}
                </Option>
              ))}
            </Select>
          </FormControl>

          {/* Coffee dropdown */}
          <FormControl error={formik.touched.coffee_id && Boolean(formik.errors.coffee_id)}>
            <FormLabel>Coffee</FormLabel>
            <Select
              name="coffee_id"
              value={formik.values.coffee_id}
              onChange={(e, val) => formik.setFieldValue("coffee_id", val)}
              onBlur={formik.handleBlur}
              placeholder={
                selectedCafeId ? "Select a coffee" : "Choose a cafe first"
              }
              disabled={!selectedCafeId}
            >
              {filteredCoffees.map((coffee) => (
                <Option key={coffee.id} value={coffee.id}>
                  {coffee.name}
                </Option>
              ))}
            </Select>
            {formik.touched.coffee_id && formik.errors.coffee_id && (
              <FormHelperText>{formik.errors.coffee_id}</FormHelperText>
            )}
          </FormControl>

          <Button
            variant="outlined"
            color="primary"
            type="button"
            onClick={() => navigate("/cafes")}
          >
            Can't find your cafe or coffee? Add one here
          </Button>

          {/* Rating */}
          <FormControl
            error={formik.touched.rating && Boolean(formik.errors.rating)}
          >
            <FormLabel>
              Rating: {formik.values.rating}/5 -{" "}
              {getRatingLabel(formik.values.rating)}
            </FormLabel>
            <Slider
              name="rating"
              value={formik.values.rating}
              onChange={(event, newValue) =>
                formik.setFieldValue("rating", newValue)
              }
              onBlur={formik.handleBlur}
              min={1}
              max={5}
              step={1}
              marks
              sx={{ mt: 1 }}
            />
            {formik.touched.rating && formik.errors.rating && (
              <FormHelperText>{formik.errors.rating}</FormHelperText>
            )}
          </FormControl>

          {/* Comment */}
          <FormControl
            error={formik.touched.comment && Boolean(formik.errors.comment)}
          >
            <FormLabel>Comment</FormLabel>
            <Textarea
              name="comment"
              value={formik.values.comment}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              placeholder="Share your thoughts about this coffee..."
              minRows={3}
              maxRows={6}
            />
            {formik.touched.comment && formik.errors.comment && (
              <FormHelperText>{formik.errors.comment}</FormHelperText>
            )}
          </FormControl>

          <Box sx={{ display: "flex", gap: 2 }}>
            <Button
              type="submit"
              variant="solid"
              color="primary"
              disabled={formik.isSubmitting}
              sx={{ flex: 1 }}
            >
              {isEditing ? "Update Note" : "Add Note"}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="outlined"
                color="neutral"
                onClick={onCancel}
                sx={{ flex: 1 }}
              >
                Cancel
              </Button>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default NoteForm;
